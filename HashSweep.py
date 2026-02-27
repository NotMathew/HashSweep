#!/usr/bin/env python3
"""
HashSweep - Duplicate File Finder & Cleaner
"""

import os
import hashlib
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import sys

# Colors - cool steel/slate palette
R    = "\033[0m"
B    = "\033[1m"
D    = "\033[2m"
IT   = "\033[3m"

STEEL   = "\033[38;5;153m"
ICE     = "\033[38;5;195m"
SLATE   = "\033[38;5;103m"
VIOLET  = "\033[38;5;141m"
MINT    = "\033[38;5;121m"
CORAL   = "\033[38;5;210m"
SILVER  = "\033[38;5;250m"
GHOST   = "\033[38;5;240m"
WHITE   = "\033[97m"
RED     = "\033[91m"
GREEN   = "\033[92m"

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    cwd = os.getcwd()
    ts  = datetime.now().strftime("%H:%M  %d %b %Y")
    print(f"""
{STEEL}  ┌───────────────────────────────────────────────────────────────┐
  │  {VIOLET}{B}HASHSWEEP{R}{STEEL}  ·  {ICE}Duplicate File Finder & Cleaner{STEEL}                │
  │                                                               │
  │  {GHOST}algo    {SILVER}SHA-256{STEEL}                                              │
  │  {GHOST}cwd     {SILVER}{cwd[:52]}{STEEL}{'…' if len(cwd)>52 else ' '*(53-len(cwd))}│
  │  {GHOST}time    {SILVER}{ts}{STEEL}                                   │
  └───────────────────────────────────────────────────────────────┘{R}
""")

def rule(n=66, char="─", color=GHOST):
    print(f"{color}{char * n}{R}")

def hdr(text):
    print(f"\n  {VIOLET}{B}◆{R}  {ICE}{B}{text}{R}")
    rule(char="·", color=SLATE)

def fmt_size(b):
    for u in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024.0: return f"{b:.2f} {u}"
        b /= 1024.0
    return f"{b:.2f} PB"

def fmt_time(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

def pause(msg="  ↵  continue"):
    input(f"\n{GHOST}{IT}{msg}{R}  ")


# DuplicateFileFinder
class DuplicateFileFinder:
    def __init__(self, directories, min_size=1, recursive=True):
        self.directories           = directories
        self.min_size              = min_size        # bytes
        self.recursive             = recursive
        self.duplicate_groups      = defaultdict(list)
        self.files_processed       = 0
        self.total_size_freed      = 0
        self.files_deleted         = 0
        self.total_duplicate_files = 0

    # Core hashing & scanning
    def get_file_hash(self, filepath, chunk_size=8192):
        """Calculate file hash using SHA-256"""
        hash_func = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except (IOError, OSError) as e:
            print(f"  {CORAL}Error reading file {filepath}: {e}{R}")
            return None

    def group_files_by_size(self):
        """Group files by their size for initial screening"""
        size_groups = defaultdict(list)
        for directory in self.directories:
            if not os.path.exists(directory):
                print(f"  {CORAL}Warning: Directory {directory} does not exist, skipping...{R}")
                continue
            print(f"  {GHOST}Scanning: {SILVER}{directory}{R}")
            if self.recursive:
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        filepath = os.path.join(root, file)
                        self._process_file(filepath, size_groups)
            else:
                for item in os.listdir(directory):
                    filepath = os.path.join(directory, item)
                    if os.path.isfile(filepath):
                        self._process_file(filepath, size_groups)
        return size_groups

    def _process_file(self, filepath, size_groups):
        """Helper function to process individual files"""
        try:
            file_size = os.path.getsize(filepath)
            if file_size >= self.min_size:
                size_groups[file_size].append(filepath)
                self.files_processed += 1
        except (OSError, IOError):
            pass

    def find_duplicates(self):
        """Find duplicate files by comparing SHA-256 hashes"""
        print(f"  {GHOST}Scanning files by size...{R}")
        size_groups = self.group_files_by_size()

        print(f"  {GHOST}Calculating SHA-256 hashes...{R}")
        potential_duplicates = 0

        for size, file_list in size_groups.items():
            if len(file_list) > 1:  # Potential duplicates
                potential_duplicates += len(file_list)
                hash_groups = defaultdict(list)

                for filepath in file_list:
                    file_hash = self.get_file_hash(filepath)
                    if file_hash:
                        hash_groups[file_hash].append(filepath)

                # Add only groups with actual duplicates
                for file_hash, duplicates in hash_groups.items():
                    if len(duplicates) > 1:
                        self.duplicate_groups[file_hash] = duplicates
                        self.total_duplicate_files += len(duplicates)

        print(f"  {GHOST}Found {SILVER}{potential_duplicates}{GHOST} files with matching sizes{R}")

    # Display
    def display_duplicate_summary(self):
        """Show summary of all duplicates found"""
        if not self.duplicate_groups:
            print(f"\n  {MINT}{B}✓  No duplicate files found!{R}")
            return False

        total_potential_space = 0
        for duplicates in self.duplicate_groups.values():
            if len(duplicates) > 1:
                total_potential_space += sum(os.path.getsize(f) for f in duplicates[1:])

        hdr("DUPLICATE FILES DETECTED")
        print(f"  {GHOST}Duplicate groups:        {VIOLET}{B}{len(self.duplicate_groups)}{R}")
        print(f"  {GHOST}Total duplicate files:   {VIOLET}{B}{self.total_duplicate_files}{R}")
        print(f"  {GHOST}Potential space to free: {MINT}{B}{fmt_size(total_potential_space)}{R}")
        rule(char="·", color=GHOST)

        return True

    # Menus
    def ask_scan_mode(self):
        """Ask user whether to scan current directory only or include subdirectories"""
        hdr("SCAN MODE SELECTION")
        print(f"  {GHOST}directory  {STEEL}{self.directories[0]}{R}\n")
        print(f"  {STEEL}1{R}  {SILVER}Current directory only{R}  {GHOST}(no subdirectories){R}")
        print(f"  {STEEL}2{R}  {SILVER}Current directory and all subdirectories{R}  {GHOST}(recursive){R}")
        rule(char="·", color=GHOST)
        while True:
            choice = input(f"\n  {STEEL}›  {R}").strip()
            if choice == "1":
                self.recursive = False
                return "Current directory only"
            elif choice == "2":
                self.recursive = True
                return "Current directory and all subdirectories"
            else:
                print(f"  {CORAL}Invalid choice! Please enter 1 or 2.{R}")

    def ask_user_action(self):
        """Ask user what action to take for duplicates"""
        hdr("ACTION")
        print(f"  {GHOST}What would you like to do with the duplicates?{R}\n")
        print(f"  {STEEL}1{R}  {SILVER}Interactive mode{R}  {GHOST}- choose which files to delete{R}")
        print(f"  {STEEL}2{R}  {SILVER}Auto-delete mode{R}  {GHOST}- keep newest files, delete older ones{R}")
        print(f"  {STEEL}3{R}  {SILVER}Skip{R}  {GHOST}- don't delete any files{R}")
        print(f"  {STEEL}4{R}  {SILVER}Quit{R}  {GHOST}- exit the program{R}")
        rule(char="·", color=GHOST)
        while True:
            choice = input(f"\n  {STEEL}›  {R}").strip()
            if choice == "1": return "interactive"
            if choice == "2": return "auto"
            if choice == "3": return "skip"
            if choice == "4": return "quit"
            print(f"  {CORAL}Invalid choice! Please enter 1, 2, 3, or 4.{R}")

    # Delete operations
    def delete_all_except(self, file_list, keep_index):
        """Delete all files except the one at keep_index"""
        file_to_keep = file_list[keep_index]
        kept_size = os.path.getsize(file_to_keep)

        print(f"  {GHOST}Keeping: {SILVER}{file_to_keep}{R}")

        for i, filepath in enumerate(file_list):
            if i != keep_index:
                try:
                    file_size = os.path.getsize(filepath)
                    os.remove(filepath)
                    self.total_size_freed += file_size
                    self.files_deleted    += 1
                    print(f"  {MINT}✓{R}  {GHOST}Deleted: {D}{filepath}{R}  {GHOST}({fmt_size(file_size)}){R}")
                except OSError as e:
                    print(f"  {CORAL}✗  Error deleting {filepath}: {e}{R}")

    def auto_delete_single_group(self, duplicates):
        """Auto-delete for a single group, keeping newest"""
        duplicates.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        file_to_keep = duplicates[0]

        print(f"  {GHOST}Auto-keeping newest: {SILVER}{file_to_keep}{R}")

        for filepath in duplicates[1:]:
            try:
                file_size = os.path.getsize(filepath)
                os.remove(filepath)
                self.total_size_freed += file_size
                self.files_deleted    += 1
                print(f"  {MINT}✓{R}  {GHOST}Deleted: {D}{filepath}{R}  {GHOST}({fmt_size(file_size)}){R}")
            except OSError as e:
                print(f"  {CORAL}✗  Error deleting {filepath}: {e}{R}")

    def interactive_delete(self):
        """Let user choose which duplicates to delete"""
        if not self.duplicate_groups:
            return

        hdr(f"INTERACTIVE MODE  ·  {len(self.duplicate_groups)} duplicate group(s)")

        for group_num, (file_hash, duplicates) in enumerate(
                list(self.duplicate_groups.items()), 1):

            # Sort by modification time (newest first)
            duplicates.sort(key=lambda x: os.path.getmtime(x), reverse=True)

            while len(duplicates) > 1:
                print(f"\n  {VIOLET}┌─  Duplicate Group {group_num} / {len(self.duplicate_groups)}{R}")
                print(f"  {VIOLET}│{R}  {GHOST}Files in this group ({len(duplicates)} files):{R}")

                for i, filepath in enumerate(duplicates, 1):
                    size  = os.path.getsize(filepath) if os.path.exists(filepath) else 0
                    mtime = fmt_time(os.path.getmtime(filepath)) if os.path.exists(filepath) else "?"
                    bullet = f"{MINT}►{R}" if i == 1 else f"{GHOST}·{R}"
                    print(f"  {VIOLET}│{R}  {STEEL}{i}{R}  {bullet}  {SILVER}{filepath}{R}")
                    print(f"  {VIOLET}│{R}      {GHOST}Size: {fmt_size(size)} | Modified: {mtime}{R}")

                print(f"  {VIOLET}└─{R}")
                rule(char="·", color=GHOST)
                print(f"  {GHOST}[number]{R}  Keep this file, delete all others")
                print(f"  {GHOST}[a]{R}       Auto-keep newest, delete older")
                print(f"  {GHOST}[s]{R}       Skip this group")
                print(f"  {GHOST}[q]{R}       Quit interactive mode")

                choice = input(f"\n  {STEEL}›  {R}").strip().lower()

                if choice == "q":
                    print(f"\n  {SLATE}Exiting interactive mode...{R}")
                    return
                elif choice == "s":
                    print(f"  {GHOST}Skipping this group...{R}")
                    break
                elif choice == "a":
                    self.auto_delete_single_group(duplicates)
                    del self.duplicate_groups[file_hash]
                    break
                elif choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(duplicates):
                        self.delete_all_except(duplicates, idx)
                        del self.duplicate_groups[file_hash]
                        break
                    else:
                        print(f"  {CORAL}Invalid number! Please choose a valid file number.{R}")
                else:
                    print(f"  {CORAL}Invalid choice! Please try again.{R}")

    def auto_delete_all(self):
        """Automatically delete all duplicates, keeping newest files"""
        if not self.duplicate_groups:
            print(f"  {GHOST}No duplicates found to delete.{R}")
            return

        hdr(f"AUTO-DELETE MODE  ·  {len(self.duplicate_groups)} group(s)")
        print(f"  {GHOST}Keeping newest files, deleting older duplicates...{R}")

        for group_num, (file_hash, duplicates) in enumerate(
                self.duplicate_groups.items(), 1):
            print(f"\n  {STEEL}--- Processing Group {group_num}/{len(self.duplicate_groups)} ---{R}")
            self.auto_delete_single_group(duplicates)

    # Final summary
    def show_final_summary(self):
        """Display comprehensive summary"""
        scan_mode = ("Current directory and all subdirectories"
                     if self.recursive else "Current directory only")

        hdr("FINAL SUMMARY")
        rows = [
            ("Scan mode",              scan_mode),
            ("Files processed",        f"{self.files_processed:,}"),
            ("Duplicate groups found", f"{len(self.duplicate_groups):,}"),
            ("Total duplicate files",  f"{self.total_duplicate_files:,}"),
            ("Files deleted",          f"{MINT}{B}{self.files_deleted:,}{R}"),
            ("Space freed",            f"{VIOLET}{B}{fmt_size(self.total_size_freed)}{R}"),
        ]

        # Calculate statistics
        if self.total_duplicate_files > 0:
            duplicate_percentage = (self.total_duplicate_files / self.files_processed * 100) \
                                   if self.files_processed else 0
            rows.append(("Duplicate percentage", f"{duplicate_percentage:.1f}%"))

        # Show remaining files
        remaining_files = self.files_processed - self.files_deleted
        rows.append(("Remaining files", f"{remaining_files:,}"))

        for label, val in rows:
            print(f"  {GHOST}{label:<26}{R}  {SILVER}{val}{R}")

        rule(char="·", color=GHOST)
        if   self.files_deleted > 0:    print(f"\n  {MINT}{B}🎉  Cleanup completed successfully!{R}")
        elif self.duplicate_groups:     print(f"\n  {SLATE}ℹ   No files were deleted (skipped mode).{R}")
        else:                           print(f"\n  {MINT}✅  No duplicate files found!{R}")


# Main
def main():
    current_dir = os.getcwd()
    directories_to_scan = [current_dir]

    clear()
    banner()

    finder = DuplicateFileFinder(
        directories=directories_to_scan,
        min_size=1024,
        recursive=True
    )

    try:
        # Step 1: Ask user about scan mode
        scan_mode = finder.ask_scan_mode()
        print(f"\n  {GHOST}Selected scan mode: {STEEL}{scan_mode}{R}")

        # Step 2: Find duplicates
        clear(); banner()
        hdr("FINDING DUPLICATES")
        print(f"\n  {GHOST}Step 1: Finding duplicates...{R}\n")
        finder.find_duplicates()

        # Step 3: Show summary and ask for action
        clear(); banner()
        if finder.display_duplicate_summary():
            action = finder.ask_user_action()

            if action == "quit":
                print(f"\n  {GHOST}Exiting program...{R}\n")
                return
            elif action == "skip":
                print(f"\n  {GHOST}Skipping file deletion...{R}")
            elif action == "auto":
                print(f"\n  {GHOST}Starting auto-delete mode...{R}")
                finder.auto_delete_all()
            elif action == "interactive":
                finder.interactive_delete()

        # Step 4: Show final summary
        clear(); banner()
        finder.show_final_summary()

    except KeyboardInterrupt:
        print(f"\n\n  {SLATE}Process interrupted by user.{R}")
        finder.show_final_summary()
    except Exception as e:
        print(f"\n  {CORAL}❌  Error: {e}{R}")
        sys.exit(1)


if __name__ == "__main__":
    main()
