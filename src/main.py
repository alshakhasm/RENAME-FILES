#!/usr/bin/env python3
"""
Main CLI interface for the Date Prefix File Renamer application.

This module provides the primary command-line interface for running the application,
including argument parsing, configuration, and workflow execution.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from src.core.session import SessionManager, SessionFactory
from src.models.enums import ValidationLevel, LogLevel, DateFormatStyle
from src.utils.logging import setup_logging, get_operation_logger
from src.utils.exceptions import DatePrefixRenamerError


def setup_argument_parser() -> argparse.ArgumentParser:
    """
    Setup command-line argument parser with all supported options.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Date Prefix File Renamer - Add creation date prefixes to files and folders",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/directory                    # Rename files in directory
  %(prog)s /path/to/directory --dry-run          # Preview changes without executing
  %(prog)s /path/to/directory --recursive        # Include subdirectories
  %(prog)s /path/to/directory --format US_DATE   # Use MM-DD-YYYY format
  %(prog)s /path/to/directory --validation strict # Use strict validation
        """
    )
    
    # Required arguments
    parser.add_argument(
        'directory',
        type=Path,
        help='Target directory to process'
    )
    
    # Operation modes
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Preview changes without executing renames'
    )
    
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        default=True,
        help='Process subdirectories recursively (default: True)'
    )
    
    parser.add_argument(
        '--no-recursive',
        action='store_false',
        dest='recursive',
        help='Process only files in target directory'
    )
    
    # Date formatting
    parser.add_argument(
        '--format', '-f',
        type=str,
        choices=['ISO_DATE', 'US_DATE', 'COMPACT', 'DDMMYYYY', 'YEAR_MONTH'],
        default='DDMMYYYY',
        help='Date prefix format style (default: DDMMYYYY = DDMMYYYY)'
    )
    
    # Validation options
    parser.add_argument(
        '--validation',
        type=str,
        choices=['strict', 'normal', 'permissive', 'disabled'],
        default='normal',
        help='Validation level for file operations (default: normal)'
    )
    
    # Safety options
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Create backup copies before renaming'
    )
    
    parser.add_argument(
        '--allow-overwrites',
        action='store_true',
        help='Allow overwriting existing files (dangerous)'
    )
    
    # Filtering options
    parser.add_argument(
        '--include-hidden',
        action='store_true',
        help='Include hidden files and directories'
    )
    
    parser.add_argument(
        '--follow-symlinks',
        action='store_true',
        help='Follow symbolic links during processing'
    )
    
    parser.add_argument(
        '--extensions',
        type=str,
        nargs='*',
        help='Filter by file extensions (e.g., --extensions .txt .jpg .pdf)'
    )
    
    parser.add_argument(
        '--exclude',
        type=str,
        nargs='*',
        help='Exclude files matching patterns (e.g., --exclude "*.tmp" "temp_*")'
    )
    
    # Logging options
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        default='info',
        help='Logging level (default: info)'
    )
    
    parser.add_argument(
        '--log-file',
        type=Path,
        help='Write logs to specified file'
    )
    
    # Output options
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress output'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--output-format',
        type=str,
        choices=['text', 'json'],
        default='text',
        help='Output format for results (default: text)'
    )
    
    # Version information
    parser.add_argument(
        '--version',
        action='version',
        version='Date Prefix File Renamer 1.0.0'
    )
    
    return parser


def configure_logging(args: argparse.Namespace) -> None:
    """
    Configure logging based on command-line arguments.
    
    Args:
        args: Parsed command-line arguments
    """
    # Map string to LogLevel enum
    log_level_mapping = {
        'debug': LogLevel.DEBUG,
        'info': LogLevel.INFO,
        'warning': LogLevel.WARNING,
        'error': LogLevel.ERROR,
        'critical': LogLevel.CRITICAL
    }
    
    log_level = log_level_mapping[args.log_level]
    
    # Setup logging
    setup_logging(
        level=log_level,
        log_file=args.log_file,
        console_output=not args.quiet,
        include_thread_info=args.verbose,
        include_process_info=args.verbose
    )


def create_session_manager(args: argparse.Namespace) -> SessionManager:
    """
    Create and configure SessionManager based on command-line arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Configured SessionManager instance
    """
    # Map validation level
    validation_mapping = {
        'strict': ValidationLevel.STRICT,
        'normal': ValidationLevel.NORMAL,
        'permissive': ValidationLevel.PERMISSIVE,
        'disabled': ValidationLevel.DISABLED
    }
    
    validation_level = validation_mapping[args.validation]
    
    # Use factory for safe configuration if strict validation
    if validation_level == ValidationLevel.STRICT:
        session_manager = SessionFactory.create_safe_session_manager()
    else:
        session_manager = SessionFactory.create_default_session_manager(validation_level)
    
    # Configure date format style
    date_format_mapping = {
        'ISO_DATE': DateFormatStyle.ISO_DATE,
        'US_DATE': DateFormatStyle.US_DATE,
        'COMPACT': DateFormatStyle.COMPACT,
        'YEAR_MONTH': DateFormatStyle.YEAR_MONTH
    }
    
    date_style = date_format_mapping[args.format]
    session_manager.date_extractor.default_style = date_style
    
    # Configure scanner options
    session_manager.file_scanner.include_hidden = args.include_hidden
    session_manager.file_scanner.follow_symlinks = args.follow_symlinks
    
    if args.extensions:
        session_manager.file_scanner.file_extensions = set(args.extensions)
    
    if args.exclude:
        session_manager.file_scanner.exclude_patterns = set(args.exclude)
    
    # Configure renamer options
    session_manager.file_renamer.create_backups = args.backup
    session_manager.file_renamer.allow_overwrites = args.allow_overwrites
    session_manager.file_renamer.dry_run_mode = args.dry_run
    
    return session_manager


def format_results_text(result, args: argparse.Namespace) -> str:
    """
    Format operation results as human-readable text.
    
    Args:
        result: OperationResult instance
        args: Command-line arguments
        
    Returns:
        Formatted text string
    """
    lines = []
    
    # Header
    mode = "DRY RUN" if args.dry_run else "EXECUTION"
    lines.append(f"\n=== Date Prefix Renamer - {mode} RESULTS ===")
    lines.append(f"Directory: {args.directory}")
    lines.append(f"Date Format: {args.format}")
    lines.append("")
    
    # Summary
    lines.append("SUMMARY:")
    lines.append(f"  Total items processed: {result.session.total_items}")
    lines.append(f"  Successful renames: {len(result.successful_renames)}")
    lines.append(f"  Failed operations: {len(result.failed_operations)}")
    lines.append(f"  Skipped items: {len(result.skipped_items)}")
    lines.append(f"  Execution time: {result.execution_time.total_seconds():.2f} seconds")
    lines.append(f"  Success rate: {result.success_rate:.1f}%")
    lines.append("")
    
    # Successful operations
    if result.successful_renames and args.verbose:
        lines.append("SUCCESSFUL RENAMES:")
        for op in result.successful_renames:
            lines.append(f"  ✓ {op.original_name} → {op.target_name}")
        lines.append("")
    
    # Failed operations
    if result.failed_operations:
        lines.append("FAILED OPERATIONS:")
        for op in result.failed_operations:
            lines.append(f"  ✗ {op.original_name}: {op.error_message or 'Unknown error'}")
        lines.append("")
    
    # Skipped items
    if result.skipped_items and args.verbose:
        lines.append("SKIPPED ITEMS:")
        for item in result.skipped_items:
            lines.append(f"  - {item.name} (already has date prefix)")
        lines.append("")
    
    return "\n".join(lines)


def format_results_json(result, args: argparse.Namespace) -> str:
    """
    Format operation results as JSON.
    
    Args:
        result: OperationResult instance
        args: Command-line arguments
        
    Returns:
        JSON string
    """
    import json
    from datetime import datetime
    
    # Create JSON-serializable data
    data = {
        'execution_mode': 'dry_run' if args.dry_run else 'execution',
        'directory': str(args.directory),
        'date_format': args.format,
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_items': result.session.total_items,
            'successful_renames': len(result.successful_renames),
            'failed_operations': len(result.failed_operations),
            'skipped_items': len(result.skipped_items),
            'execution_time_seconds': result.execution_time.total_seconds(),
            'success_rate_percent': result.success_rate
        },
        'successful_renames': [
            {
                'original_name': op.original_name,
                'target_name': op.target_name,
                'operation_type': str(op.operation_type)
            } for op in result.successful_renames
        ],
        'failed_operations': [
            {
                'original_name': op.original_name,
                'error_message': op.error_message or 'Unknown error'
            } for op in result.failed_operations
        ],
        'skipped_items': [
            {
                'name': item.name,
                'reason': 'already_has_date_prefix'
            } for item in result.skipped_items
        ]
    }
    
    return json.dumps(data, indent=2)


def progress_callback(phase: str, current: int, total: int, message: str):
    """Progress callback for operation updates."""
    if total > 0:
        percentage = (current / total) * 100
        print(f"\r{phase}: [{percentage:6.1f}%] {message}", end='', flush=True)
    else:
        print(f"\r{phase}: {message}", end='', flush=True)


def main() -> int:
    """
    Main entry point for the CLI application.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Parse command-line arguments
        parser = setup_argument_parser()
        args = parser.parse_args()
        
        # Validate target directory
        if not args.directory.exists():
            print(f"Error: Directory does not exist: {args.directory}", file=sys.stderr)
            return 1
        
        if not args.directory.is_dir():
            print(f"Error: Path is not a directory: {args.directory}", file=sys.stderr)
            return 1
        
        # Configure logging
        configure_logging(args)
        logger = get_operation_logger(__name__)
        
        # Create session manager
        session_manager = create_session_manager(args)
        
        # Setup progress callback if not quiet
        progress_cb = None if args.quiet else progress_callback
        
        # Print start message
        if not args.quiet:
            mode = "DRY RUN" if args.dry_run else "EXECUTION"
            print(f"Date Prefix File Renamer - {mode} MODE")
            print(f"Processing directory: {args.directory}")
            print(f"Date format: {args.format}")
            print(f"Recursive: {args.recursive}")
            print()
        
        # Run the complete workflow
        with session_manager:
            result = session_manager.run_complete_workflow(
                target_directory=args.directory,
                is_dry_run=args.dry_run,
                recursive=args.recursive,
                progress_callback=progress_cb
            )
        
        # Clear progress line
        if not args.quiet:
            print("\r" + " " * 80 + "\r", end='')
        
        # Format and display results
        if args.output_format == 'json':
            print(format_results_json(result, args))
        else:
            print(format_results_text(result, args))
        
        # Return appropriate exit code
        return 0 if result.success_rate == 100.0 else 1
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 130  # Standard exit code for SIGINT
        
    except DatePrefixRenamerError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
        
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if '--verbose' in sys.argv:
            import traceback
            traceback.print_exc()
        return 2


if __name__ == '__main__':
    sys.exit(main())