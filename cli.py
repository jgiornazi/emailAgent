"""
EmailAgent CLI - Job Application Tracker

A command-line tool for tracking job applications from Gmail emails.

Commands:
    auth    Authentication commands (login, logout, status)
    job     Job tracking commands (scan, list, show, export, stats)
    config  Configuration commands (show, validate)

Usage:
    emailagent auth login       # Authenticate with Gmail
    emailagent job scan         # Scan for job emails
    emailagent job list         # List all applications
    emailagent --help           # Show help
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from core import (
    Config,
    load_config,
    save_default_config,
    ensure_directories,
    validate_config,
    get_default_config_path,
    setup_logger,
    get_logger,
    get_credentials,
    get_gmail_service,
    check_auth_status,
    logout as auth_logout,
    AuthenticationError,
    CredentialsNotFoundError,
    GmailClient,
    GmailAPIError,
    should_delete_email,
)

from job_tracker import (
    ExcelStorage,
    create_excel_storage,
    format_summary_table,
    extract_email_info,
    classify_email,
    STATUS_HIERARCHY,
)

# =============================================================================
# CLI Application Setup
# =============================================================================

app = typer.Typer(
    name="emailagent",
    help="Automated job application tracker that scans Gmail for job-related emails.",
    add_completion=False,
    no_args_is_help=True,
)

auth_app = typer.Typer(help="Authentication commands", no_args_is_help=True)
job_app = typer.Typer(help="Job tracking commands", no_args_is_help=True)
config_app = typer.Typer(help="Configuration commands", no_args_is_help=True)

app.add_typer(auth_app, name="auth")
app.add_typer(job_app, name="job")
app.add_typer(config_app, name="config")

console = Console()


# =============================================================================
# Helper Functions
# =============================================================================

def get_config() -> Config:
    """Load configuration, creating default if needed."""
    config_path = get_default_config_path()

    if not config_path.exists():
        ensure_directories()
        save_default_config(config_path)
        console.print(f"[dim]Created default config at {config_path}[/dim]")

    return load_config(config_path)


def show_error(message: str) -> None:
    """Display error message."""
    console.print(f"[red][/red] Error: {message}")


def show_success(message: str) -> None:
    """Display success message."""
    console.print(f"[green][/green] {message}")


def show_warning(message: str) -> None:
    """Display warning message."""
    console.print(f"[yellow][/yellow] {message}")


def show_info(message: str) -> None:
    """Display info message."""
    console.print(f"[blue][/blue] {message}")


def format_status(status: str) -> str:
    """Format status with color."""
    colors = {
        'Applied': 'blue',
        'Interviewing': 'yellow',
        'Rejected': 'red',
        'Offer': 'green',
    }
    color = colors.get(status, 'white')
    return f"[{color}]{status}[/{color}]"


def format_confidence(confidence: str) -> str:
    """Format confidence with color."""
    colors = {
        'high': 'green',
        'medium': 'yellow',
        'low': 'red',
    }
    color = colors.get(confidence, 'white')
    return f"[{color}]{confidence}[/{color}]"


# =============================================================================
# Auth Commands
# =============================================================================

@auth_app.command("login")
def auth_login(
    force: bool = typer.Option(False, "--force", "-f", help="Force re-authentication"),
):
    """
    Authenticate with Gmail using OAuth 2.0.

    Opens browser for Google authentication. User grants permissions
    for Gmail API access. Credentials are saved locally.
    """
    config = get_config()

    credentials_path = Path(config.gmail.credentials_path).expanduser()
    token_path = Path(config.gmail.token_path).expanduser()

    if not credentials_path.exists():
        show_error(
            f"Gmail credentials not found at: {credentials_path}\n\n"
            "To set up Gmail API credentials:\n"
            "  1. Go to https://console.cloud.google.com\n"
            "  2. Create a project and enable Gmail API\n"
            "  3. Create OAuth credentials (Desktop app)\n"
            "  4. Download credentials.json\n"
            f"  5. Save to: {credentials_path}\n\n"
            "See SETUP.md for detailed instructions."
        )
        raise typer.Exit(1)

    try:
        console.print("Opening browser for Google authentication...")

        creds = get_credentials(credentials_path, token_path, force_refresh=force)

        # Get user email from Gmail API
        service = get_gmail_service(credentials_path, token_path)
        profile = service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress', 'unknown')

        show_success(f"Successfully authenticated as [bold]{email}[/bold]")
        show_success(f"Token saved to {token_path}")

    except CredentialsNotFoundError as e:
        show_error(str(e))
        raise typer.Exit(1)
    except AuthenticationError as e:
        show_error(f"Authentication failed: {e}")
        raise typer.Exit(2)
    except Exception as e:
        show_error(f"Unexpected error: {e}")
        raise typer.Exit(1)


@auth_app.command("logout")
def auth_logout_cmd(
    revoke: bool = typer.Option(False, "--revoke", help="Revoke token with Google"),
):
    """
    Log out and delete saved credentials.

    Deletes the local token file. Use --revoke to also revoke
    the token with Google (more thorough).
    """
    config = get_config()
    token_path = Path(config.gmail.token_path).expanduser()

    if not token_path.exists():
        show_info("No token found. Already logged out.")
        return

    try:
        auth_logout(token_path, revoke=revoke)
        show_success("Token deleted successfully")
        show_info("Run 'emailagent auth login' to authenticate again")

    except Exception as e:
        show_error(f"Logout failed: {e}")
        raise typer.Exit(1)


@auth_app.command("status")
def auth_status():
    """Check current authentication status."""
    config = get_config()

    credentials_path = Path(config.gmail.credentials_path).expanduser()
    token_path = Path(config.gmail.token_path).expanduser()

    # Check credentials
    if not credentials_path.exists():
        show_error(f"Credentials not found: {credentials_path}")
        console.print("[dim]Run 'emailagent auth login' to set up authentication[/dim]")
        raise typer.Exit(1)

    # Check token
    if not token_path.exists():
        show_warning("Not authenticated")
        console.print("[dim]Run 'emailagent auth login' to authenticate[/dim]")
        raise typer.Exit(1)

    try:
        status = check_auth_status(token_path)

        if status['authenticated']:
            show_success(f"Authenticated as [bold]{status.get('email', 'unknown')}[/bold]")

            if status.get('expires_at'):
                console.print(f"[dim]Token expires: {status['expires_at']}[/dim]")
        else:
            show_warning("Token expired or invalid")
            console.print("[dim]Run 'emailagent auth login' to re-authenticate[/dim]")
            raise typer.Exit(1)

    except Exception as e:
        show_error(f"Status check failed: {e}")
        raise typer.Exit(1)


# =============================================================================
# Job Commands
# =============================================================================

@job_app.command("scan")
def job_scan(
    preview: bool = typer.Option(False, "--preview", "-p", help="Preview without deleting"),
    use_ai: bool = typer.Option(False, "--use-ai", help="Enable AI extraction (Ollama)"),
    no_ai: bool = typer.Option(True, "--no-ai", help="Pattern-only mode (default)"),
    max_emails: int = typer.Option(10000, "--max-emails", "-m", help="Maximum emails to process"),
    since: Optional[str] = typer.Option(None, "--since", help="Only process emails after date (YYYY-MM-DD)"),
    confirm: bool = typer.Option(True, "--confirm-delete/--no-confirm", help="Require confirmation before delete"),
):
    """
    Scan Gmail for job-related emails.

    Extracts company, position, and status information from job emails.
    Updates Excel file and optionally deletes processed emails.

    Examples:
        emailagent job scan --preview    # Preview without deleting
        emailagent job scan --use-ai     # Use AI for better accuracy
        emailagent job scan --since 2026-01-01  # Process recent emails only
    """
    config = get_config()
    setup_logger(
        level=config.logging.level,
        log_directory=config.logging.log_directory,
        max_size_mb=config.logging.max_log_size_mb,
    )

    # Parse since date
    since_date = None
    if since:
        try:
            since_date = datetime.strptime(since, '%Y-%m-%d')
        except ValueError:
            show_error(f"Invalid date format: {since}. Use YYYY-MM-DD")
            raise typer.Exit(12)
    elif preview:
        # Default to 24 hours ago for preview mode to limit scan scope
        since_date = datetime.now() - timedelta(days=1)
        show_info(f"Preview mode: defaulting to --since {since_date.strftime('%Y-%m-%d')}")

    # Override AI setting
    if use_ai:
        config.extraction.use_ai = True

    # Authenticate
    try:
        credentials_path = Path(config.gmail.credentials_path).expanduser()
        token_path = Path(config.gmail.token_path).expanduser()
        creds = get_credentials(credentials_path, token_path)
        service = get_gmail_service(credentials_path, token_path)
    except AuthenticationError as e:
        show_error(f"Authentication required: {e}")
        console.print("[dim]Run 'emailagent auth login' first[/dim]")
        raise typer.Exit(2)

    # Initialize Gmail client
    gmail = GmailClient(
        service,
        batch_size=config.gmail.batch_size,
        requests_per_second=config.gmail.requests_per_second,
    )

    # Initialize Excel storage
    storage = create_excel_storage(config.to_dict())
    storage.initialize()

    console.print("\n[bold]Scanning Gmail for job emails...[/bold]")

    # Search for emails
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task("Searching for job emails...", total=None)
            email_ids = gmail.search_job_emails(max_results=max_emails, since_date=since_date)

        console.print(f"Found [bold]{len(email_ids):,}[/bold] job-related emails")

        if not email_ids:
            show_info("No job emails found matching criteria")
            return

    except GmailAPIError as e:
        show_error(f"Gmail API error: {e}")
        raise typer.Exit(3)

    # Process emails
    results = {
        'total': len(email_ids),
        'processed': 0,
        'new_companies': 0,
        'updated': 0,
        'conflicts': 0,
        'to_delete': [],
        'to_keep': [],
        'status_counts': {s: 0 for s in STATUS_HIERARCHY},
    }

    console.print("\n[bold]Processing emails...[/bold]")

    # Fetch all emails first
    emails_data = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching email details", total=len(email_ids))

        for email in gmail.fetch_emails(email_ids):
            emails_data.append(email)
            progress.update(task, advance=1)

    console.print(f"Fetched [bold]{len(emails_data)}[/bold] emails")

    # Process emails
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing", total=len(emails_data))

        for i, email in enumerate(emails_data):
            try:
                # Convert to dict for extraction
                email_dict = {
                    'id': email.id,
                    'subject': email.subject,
                    'from': email.sender,
                    'body': email.body,
                    'snippet': email.snippet,
                    'date': email.date,
                }

                # Extract information
                extraction = extract_email_info(
                    email_dict,
                    {'use_ai': config.extraction.use_ai}
                )

                # Classify status
                extraction = classify_email(extraction, email_dict)

                # Log email details for debugging
                get_logger("scan").info(
                    f"ID: {email.id} | From: {email.sender} | "
                    f"Subject: {email.subject[:80]} | "
                    f"Status: {extraction.status} | Company: {extraction.company}"
                )

                # Update Excel
                update_result = storage.add_or_update(extraction)

                # Track results
                results['processed'] += 1
                results['status_counts'][extraction.status] += 1

                if update_result.is_new_row:
                    results['new_companies'] += 1
                elif update_result.is_update:
                    results['updated'] += 1
                if update_result.is_conflict:
                    results['conflicts'] += 1

                # Determine if should delete
                email_text = f"{email.subject} {email.body}"
                deletion_result = should_delete_email(
                    status=extraction.status,
                    email_text=email_text,
                    is_conflict=update_result.is_conflict,
                    is_starred=email.is_starred,
                    has_attachments=email.has_attachments,
                    delete_applied=config.deletion.delete_applied,
                    delete_rejected=config.deletion.delete_rejected,
                )
                if deletion_result.should_delete:
                    results['to_delete'].append(email.id)
                else:
                    results['to_keep'].append(email.id)

                # Save periodically
                if (i + 1) % 100 == 0:
                    storage.save_if_needed(100)

            except Exception as e:
                get_logger("cli").error(f"Error processing {email.id}: {e}")
                continue

            progress.update(task, advance=1)

    # Final save
    storage.save()

    # Show summary
    console.print("\n")
    summary_panel = Panel(
        f"""[bold]Processing Complete[/bold]

Total emails processed: {results['processed']:,}

[bold]Status Breakdown:[/bold]
  Applied:      {results['status_counts']['Applied']:>5} emails {"(will be deleted)" if not preview else ""}
  Interviewing: {results['status_counts']['Interviewing']:>5} emails [green](KEPT)[/green]
  Rejected:     {results['status_counts']['Rejected']:>5} emails {"(will be deleted)" if not preview else ""}
  Offer:        {results['status_counts']['Offer']:>5} emails [green](KEPT)[/green]

[bold]Excel Updates:[/bold]
  New companies: {results['new_companies']}
  Updated:       {results['updated']}
  Conflicts:     {results['conflicts']}

[bold]Deletion Summary:[/bold]
  To delete: {len(results['to_delete']):,} emails
  To keep:   {len(results['to_keep']):,} emails

[dim]Data saved to: {storage.file_path}[/dim]""",
        title="Summary",
        border_style="blue",
    )
    console.print(summary_panel)

    # Handle deletion
    if preview:
        show_info("Preview mode - no emails deleted")
        console.print("[dim]Run without --preview to delete emails[/dim]")
        return

    if not results['to_delete']:
        show_info("No emails to delete")
        return

    # Confirmation
    if confirm:
        console.print(f"\n[bold yellow]Ready to delete {len(results['to_delete']):,} emails?[/bold yellow]")
        console.print("[dim]Emails will be moved to Trash (30-day recovery)[/dim]")

        confirmed = typer.confirm("Proceed with deletion?", default=True)
        if not confirmed:
            show_warning("Deletion cancelled")
            raise typer.Exit(5)

    # Delete emails
    console.print("\n[bold]Deleting emails...[/bold]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Deleting", total=len(results['to_delete']))

        deleted_count = 0
        for email_id in results['to_delete']:
            try:
                if gmail.trash_email(email_id):
                    deleted_count += 1
            except Exception as e:
                get_logger("cli").error(f"Failed to delete {email_id}: {e}")

            progress.update(task, advance=1)

    show_success(f"Deleted {deleted_count:,} emails")
    console.print("\n[dim]Recovery options:[/dim]")
    console.print("  1. Gmail web: Trash folder -> Select -> Move to Inbox")
    console.print("  2. Undo command: emailagent job undo-last")
    console.print("  3. Auto-delete: Gmail permanently deletes after 30 days")


@job_app.command("list")
def job_list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    company: Optional[str] = typer.Option(None, "--company", "-c", help="Filter by company (partial match)"),
    action_required: bool = typer.Option(False, "--action-required", "-a", help="Show only Interviewing/Offer"),
    conflicts: bool = typer.Option(False, "--conflicts", help="Show only conflicts"),
    limit: int = typer.Option(50, "--limit", "-n", help="Maximum rows to show"),
    format_: str = typer.Option("table", "--format", "-f", help="Output format: table, csv, json"),
):
    """
    List job applications from Excel.

    Examples:
        emailagent job list                    # List all
        emailagent job list --status Offer     # Filter by status
        emailagent job list --action-required  # Show actionable items
    """
    config = get_config()

    # Initialize storage
    storage = create_excel_storage(config.to_dict())

    try:
        storage.initialize()
    except FileNotFoundError:
        show_error("No job applications file found")
        console.print("[dim]Run 'emailagent job scan' to create one[/dim]")
        raise typer.Exit(4)

    # Get applications
    apps = storage.get_all_applications()

    if not apps:
        show_info("No applications found")
        return

    # Filter
    if status:
        apps = [a for a in apps if a.status.lower() == status.lower()]

    if company:
        company_lower = company.lower()
        apps = [a for a in apps if company_lower in a.company.lower()]

    if action_required:
        apps = [a for a in apps if a.status in ['Interviewing', 'Offer']]

    if conflicts:
        apps = [a for a in apps if a.has_conflict]

    # Sort by date (most recent first)
    apps.sort(key=lambda a: a.date_last or datetime.min, reverse=True)

    # Limit
    apps = apps[:limit]

    if not apps:
        show_info("No applications match filters")
        return

    # Output
    if format_ == "csv":
        import csv
        import sys
        writer = csv.writer(sys.stdout)
        writer.writerow(['Company', 'Position', 'Status', 'Last Update', 'Notes'])
        for a in apps:
            writer.writerow([
                a.company,
                a.position,
                a.status,
                a.date_last.strftime('%Y-%m-%d') if a.date_last else '',
                a.notes,
            ])

    elif format_ == "json":
        import json
        data = [a.to_dict() for a in apps]
        print(json.dumps(data, indent=2))

    else:
        # Table format
        table = Table(title=f"Job Applications ({len(apps)} shown)")

        table.add_column("Company", style="cyan", no_wrap=True)
        table.add_column("Position", style="white")
        table.add_column("Status", justify="center")
        table.add_column("Last Update", justify="center")
        table.add_column("Notes", style="dim")

        for a in apps:
            status_display = format_status(a.status)
            date_str = a.date_last.strftime('%Y-%m-%d') if a.date_last else '-'
            notes_preview = a.notes[:30] + "..." if len(a.notes) > 30 else a.notes

            # Highlight conflicts
            if a.has_conflict:
                notes_preview = f"[red]{notes_preview}[/red]"

            table.add_row(
                a.company,
                a.position,
                status_display,
                date_str,
                notes_preview,
            )

        console.print(table)

        # Summary
        stats = storage.get_statistics()
        console.print(f"\n[dim]Status: Applied={stats['status_counts']['Applied']} | "
                     f"Interviewing={stats['status_counts']['Interviewing']} | "
                     f"Rejected={stats['status_counts']['Rejected']} | "
                     f"Offer={stats['status_counts']['Offer']}[/dim]")


@job_app.command("show")
def job_show(
    company_name: str = typer.Argument(..., help="Company name (partial match)"),
):
    """
    Show detailed information for a company application.

    Example:
        emailagent job show "TechCorp"
    """
    config = get_config()
    storage = create_excel_storage(config.to_dict())

    try:
        storage.initialize()
    except FileNotFoundError:
        show_error("No job applications file found")
        raise typer.Exit(4)

    # Find company
    apps = storage.get_all_applications()
    company_lower = company_name.lower()
    matches = [a for a in apps if company_lower in a.company.lower()]

    if not matches:
        show_error(f"No company found matching '{company_name}'")
        raise typer.Exit(1)

    if len(matches) > 1:
        console.print(f"[yellow]Multiple matches found:[/yellow]")
        for a in matches:
            console.print(f"  - {a.company}")
        console.print("[dim]Please be more specific[/dim]")
        return

    app = matches[0]

    # Display details
    console.print(Panel(
        f"""[bold cyan]{app.company}[/bold cyan] - {app.position}

[bold]Status:[/bold]          {format_status(app.status)}
[bold]Confidence:[/bold]      {format_confidence(app.confidence)}
[bold]Date First Seen:[/bold] {app.date_first.strftime('%Y-%m-%d') if app.date_first else 'N/A'}
[bold]Date Last Update:[/bold]{app.date_last.strftime('%Y-%m-%d') if app.date_last else 'N/A'}

[bold]Email IDs:[/bold]
{chr(10).join(f'  - {eid}' for eid in app.email_ids) if app.email_ids else '  None'}

[bold]Notes:[/bold]
  {app.notes or 'None'}
""",
        border_style="blue",
    ))


@job_app.command("stats")
def job_stats():
    """Show application statistics and insights."""
    config = get_config()
    storage = create_excel_storage(config.to_dict())

    try:
        storage.initialize()
    except FileNotFoundError:
        show_error("No job applications file found")
        raise typer.Exit(4)

    stats = storage.get_statistics()
    total = stats['total_companies']

    if total == 0:
        show_info("No applications found")
        return

    # Calculate rates
    response_count = stats['status_counts']['Interviewing'] + stats['status_counts']['Rejected'] + stats['status_counts']['Offer']
    response_rate = (response_count / total * 100) if total > 0 else 0
    interview_rate = (stats['status_counts']['Interviewing'] / total * 100) if total > 0 else 0
    offer_rate = (stats['status_counts']['Offer'] / total * 100) if total > 0 else 0

    console.print(Panel(
        f"""[bold]JOB APPLICATION STATISTICS[/bold]

Total Companies: [bold]{total}[/bold]

[bold]Status Breakdown:[/bold]
  Applied:      {stats['status_counts']['Applied']:>5} ({stats['status_counts']['Applied']/total*100:.1f}%)
  Interviewing: {stats['status_counts']['Interviewing']:>5} ({interview_rate:.1f}%)
  Rejected:     {stats['status_counts']['Rejected']:>5} ({stats['status_counts']['Rejected']/total*100:.1f}%)
  Offer:        {stats['status_counts']['Offer']:>5} ({offer_rate:.1f}%)

[bold]Response Rate:[/bold]     {response_rate:.1f}% ({response_count} responses)
[bold]Interview Rate:[/bold]    {interview_rate:.1f}%
[bold]Offer Rate:[/bold]        {offer_rate:.1f}%

[bold]Confidence Levels:[/bold]
  High:   {stats['confidence_counts']['high']:>5}
  Medium: {stats['confidence_counts']['medium']:>5}
  Low:    {stats['confidence_counts']['low']:>5}

[bold]Conflicts:[/bold] {stats['conflict_count']}
""",
        title="Statistics",
        border_style="green",
    ))


@job_app.command("export")
def job_export(
    format_: str = typer.Option("csv", "--format", "-f", help="Export format: csv, json"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
):
    """
    Export job applications to file.

    Examples:
        emailagent job export --format csv --output applications.csv
        emailagent job export --format json --status Offer
    """
    config = get_config()
    storage = create_excel_storage(config.to_dict())

    try:
        storage.initialize()
    except FileNotFoundError:
        show_error("No job applications file found")
        raise typer.Exit(4)

    # Generate output path if not specified
    if not output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output = f"job_applications_{timestamp}.{format_}"

    # Export
    try:
        if format_ == "csv":
            path = storage.export_to_csv(output)
        elif format_ == "json":
            path = storage.export_to_json(output)
        else:
            show_error(f"Unknown format: {format_}")
            raise typer.Exit(12)

        show_success(f"Exported to {path}")

    except Exception as e:
        show_error(f"Export failed: {e}")
        raise typer.Exit(4)


@job_app.command("update")
def job_update(
    company_name: str = typer.Argument(..., help="Company name"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="New status"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Add/update notes"),
    clear_conflict: bool = typer.Option(False, "--clear-conflict", help="Remove conflict flag"),
    force: bool = typer.Option(False, "--force", help="Force update (bypass hierarchy)"),
):
    """
    Manually update a job application.

    Examples:
        emailagent job update "TechCorp" --status Offer
        emailagent job update "TechCorp" --notes "Phone screen scheduled"
        emailagent job update "TechCorp" --clear-conflict
    """
    config = get_config()
    storage = create_excel_storage(config.to_dict())

    try:
        storage.initialize()
    except FileNotFoundError:
        show_error("No job applications file found")
        raise typer.Exit(4)

    # Find company
    row = storage.find_company(company_name)
    if not row:
        show_error(f"Company not found: {company_name}")
        raise typer.Exit(1)

    updated = False

    # Update status
    if status:
        result = storage.manual_status_update(company_name, status, force=force)
        if result.success:
            show_success(f"Status updated: {result.old_status} -> {result.new_status}")
            updated = True
        else:
            show_error(result.message)
            if result.is_conflict:
                console.print("[dim]Use --force to override hierarchy rules[/dim]")
            raise typer.Exit(1)

    # Update notes
    if notes:
        if storage.update_notes(company_name, notes):
            show_success("Notes updated")
            updated = True
        else:
            show_error("Failed to update notes")

    # Clear conflict
    if clear_conflict:
        if storage.clear_conflict(company_name):
            show_success("Conflict flag cleared")
            updated = True
        else:
            show_error("Failed to clear conflict")

    if updated:
        storage.save()
    else:
        show_info("No changes made")


@job_app.command("undo-last")
def job_undo_last():
    """
    Restore emails from the last deletion batch.

    Moves emails back from Trash to Inbox.
    """
    config = get_config()

    # Authenticate
    try:
        credentials_path = Path(config.gmail.credentials_path).expanduser()
        token_path = Path(config.gmail.token_path).expanduser()
        creds = get_credentials(credentials_path, token_path)
        service = get_gmail_service(credentials_path, token_path)
    except AuthenticationError as e:
        show_error(f"Authentication required: {e}")
        raise typer.Exit(2)

    # Initialize Gmail client
    gmail = GmailClient(service)

    # Import deleter for undo functionality
    from core.deleter import EmailDeleter

    deleter = EmailDeleter(gmail)

    # Get last batch info
    batch_info = deleter.get_last_batch()

    if not batch_info:
        show_error("No deletion batch found to undo")
        console.print("[dim]No recent deletions recorded[/dim]")
        raise typer.Exit(1)

    email_ids = batch_info.get("email_ids", [])
    batch_id = batch_info.get("batch_id", "unknown")
    timestamp = batch_info.get("timestamp", "unknown")

    console.print(f"[bold]Found deletion batch:[/bold]")
    console.print(f"  Batch ID: {batch_id}")
    console.print(f"  Timestamp: {timestamp}")
    console.print(f"  Emails: {len(email_ids)}")
    console.print()

    if not email_ids:
        show_info("No emails to restore")
        return

    # Confirmation
    confirmed = typer.confirm(f"Restore {len(email_ids)} emails from Trash?", default=True)
    if not confirmed:
        show_warning("Undo cancelled")
        raise typer.Exit(5)

    # Restore emails
    console.print("\n[bold]Restoring emails from Trash...[/bold]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Restoring", total=len(email_ids))

        restored_count = 0
        failed = []

        for email_id in email_ids:
            try:
                # Use Gmail API to untrash
                service.users().messages().untrash(
                    userId='me',
                    id=email_id
                ).execute()
                restored_count += 1
            except Exception as e:
                get_logger("cli").error(f"Failed to restore {email_id}: {e}")
                failed.append(email_id)

            progress.update(task, advance=1)

    show_success(f"Restored {restored_count} emails")

    if failed:
        show_warning(f"Failed to restore {len(failed)} emails")
        console.print("[dim]Some emails may have been permanently deleted[/dim]")


# =============================================================================
# Config Commands
# =============================================================================

@config_app.command("show")
def config_show():
    """Display current configuration."""
    config = get_config()

    console.print(Panel(
        f"""[bold]Gmail:[/bold]
  credentials: {config.gmail.credentials_path}
  token: {config.gmail.token_path}
  max_results: {config.gmail.max_results_per_query}

[bold]Extraction:[/bold]
  use_ai: {config.extraction.use_ai}
  confidence_threshold: {config.extraction.confidence_threshold}

[bold]Excel:[/bold]
  file_path: {config.excel.file_path}
  auto_backup: {config.excel.auto_backup}

[bold]Deletion:[/bold]
  delete_applied: {config.deletion.delete_applied}
  delete_rejected: {config.deletion.delete_rejected}
  require_confirmation: {config.deletion.require_confirmation}

[bold]Logging:[/bold]
  level: {config.logging.level}
  directory: {config.logging.log_directory}
""",
        title="Configuration",
        border_style="blue",
    ))


@config_app.command("validate")
def config_validate():
    """Validate configuration file."""
    config = get_config()

    console.print("[bold]Validating configuration...[/bold]\n")

    errors, warnings = validate_config(config)

    if not errors and not warnings:
        show_success("Configuration is valid")
        return

    for error in errors:
        show_error(error)

    for warning in warnings:
        show_warning(warning)

    if errors:
        console.print(f"\n[red]Configuration has {len(errors)} error(s)[/red]")
        raise typer.Exit(11)
    else:
        console.print(f"\n[yellow]Configuration has {len(warnings)} warning(s)[/yellow]")


# =============================================================================
# Version and Help
# =============================================================================

def version_callback(value: bool):
    if value:
        console.print("[bold]EmailAgent[/bold] v1.0.0")
        console.print("Job Application Tracker")
        console.print("Python 3.11+")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    verbose: bool = typer.Option(
        False, "--verbose",
        help="Enable verbose logging",
    ),
):
    """
    EmailAgent - Automated Job Application Tracker

    Scans your Gmail for job-related emails, extracts company and status
    information, and stores it in an Excel file.

    Get started:
        emailagent auth login     # Authenticate with Gmail
        emailagent job scan       # Scan for job emails

    For help on a specific command:
        emailagent <command> --help
    """
    if verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    app()
