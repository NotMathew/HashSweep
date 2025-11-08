import os
import hashlib
from pathlib import Path
from collections import defaultdict
import sys

class DuplicateFileFinder:
    def __init__(self, directories, min_size=1, recursive=True):
        self.directories = directories
        self.min_size = min_size  # in bytes
        self.recursive = recursive
        self.duplicate_groups = defaultdict(list)
        self.files_processed = 0
        self.total_size_freed = 0
        self.files_deleted = 0
        self.total_duplicate_files = 0
        
    def get_file_hash(self, filepath, chunk_size=8192):
        """Calculate file hash using SHA-256"""
        hash_func = hashlib.sha256()
        
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except (IOError, OSError) as e:
            print(f"Error reading file {filepath}: {e}")
            return None
    
    def group_files_by_size(self):
        """Group files by their size for initial screening"""
        size_groups = defaultdict(list)
        
        for directory in self.directories:
            if not os.path.exists(directory):
                print(f"Warning: Directory {directory} does not exist, skipping...")
                continue
                
            print(f"Scanning: {directory}")
            
            if self.recursive:
                # Scan current directory and all subdirectories
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        filepath = os.path.join(root, file)
                        self._process_file(filepath, size_groups)
            else:
                # Scan only the current directory (no subdirectories)
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
        print("Scanning files by size...")
        size_groups = self.group_files_by_size()
        
        print("Calculating SHA-256 hashes...")
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
        
        print(f"Found {potential_duplicates} files with matching sizes")
    
    def format_size(self, size_bytes):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def display_duplicate_summary(self):
        """Show summary of all duplicates found"""
        if not self.duplicate_groups:
            print("No duplicate files found!")
            return False
            
        total_potential_space = 0
        for duplicates in self.duplicate_groups.values():
            if len(duplicates) > 1:
                total_potential_space += sum(os.path.getsize(f) for f in duplicates[1:])
        
        print(f"\n{'='*80}")
        print("DUPLICATE FILES DETECTED")
        print(f"{'='*80}")
        print(f"Duplicate groups:     {len(self.duplicate_groups)}")
        print(f"Total duplicate files: {self.total_duplicate_files}")
        print(f"Potential space to free: {self.format_size(total_potential_space)}")
        print(f"{'='*80}")
        
        return True
    
    def ask_scan_mode(self):
        """Ask user whether to scan current directory only or include subdirectories"""
        print("\n📁 Scan Mode Selection")
        print("1. Current directory only (no subdirectories)")
        print("2. Current directory and all subdirectories (recursive)")
        
        while True:
            choice = input("\nEnter your choice (1-2): ").strip()
            
            if choice == '1':
                self.recursive = False
                return "Current directory only"
            elif choice == '2':
                self.recursive = True
                return "Current directory and all subdirectories"
            else:
                print("Invalid choice! Please enter 1 or 2.")
    
    def ask_user_action(self):
        """Ask user what action to take for duplicates"""
        print("\nWhat would you like to do with the duplicates?")
        print("1. Interactive mode - Choose which files to delete")
        print("2. Auto-delete mode - Keep newest files, delete older ones")
        print("3. Skip - Don't delete any files")
        print("4. Quit - Exit the program")
        
        while True:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                return 'interactive'
            elif choice == '2':
                return 'auto'
            elif choice == '3':
                return 'skip'
            elif choice == '4':
                return 'quit'
            else:
                print("Invalid choice! Please enter 1, 2, 3, or 4.")
    
    def interactive_delete(self):
        """Let user choose which duplicates to delete"""
        if not self.duplicate_groups:
            return
        
        print(f"\nStarting interactive mode for {len(self.duplicate_groups)} duplicate groups...")
        
        for group_num, (file_hash, duplicates) in enumerate(list(self.duplicate_groups.items()), 1):
            print(f"\n{'='*60}")
            print(f"Duplicate Group {group_num}/{len(self.duplicate_groups)}")
            print(f"{'='*60}")
            
            # Sort by modification time (newest first)
            duplicates.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            while len(duplicates) > 1:
                print(f"\nFiles in this group ({len(duplicates)} files):")
                for i, filepath in enumerate(duplicates, 1):
                    size = os.path.getsize(filepath)
                    mtime = os.path.getmtime(filepath)
                    from datetime import datetime
                    mod_time = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"  {i}. {filepath}")
                    print(f"      Size: {self.format_size(size)} | Modified: {mod_time}")
                
                print(f"\nOptions for this group:")
                print("  [number] - Keep this file, delete all others")
                print("  a - Auto-keep newest, delete older")
                print("  s - Skip this group")
                print("  q - Quit interactive mode")
                
                choice = input("\nEnter your choice: ").strip().lower()
                
                if choice == 'q':
                    print("Exiting interactive mode...")
                    return
                elif choice == 's':
                    print("Skipping this group...")
                    break
                elif choice == 'a':
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
                        print("Invalid number! Please choose a valid file number.")
                else:
                    print("Invalid choice! Please try again.")
    
    def delete_all_except(self, file_list, keep_index):
        """Delete all files except the one at keep_index"""
        file_to_keep = file_list[keep_index]
        kept_size = os.path.getsize(file_to_keep)
        
        print(f"Keeping: {file_to_keep}")
        
        for i, filepath in enumerate(file_list):
            if i != keep_index:
                try:
                    file_size = os.path.getsize(filepath)
                    os.remove(filepath)
                    self.total_size_freed += file_size
                    self.files_deleted += 1
                    print(f"✓ Deleted: {filepath} ({self.format_size(file_size)})")
                except OSError as e:
                    print(f"✗ Error deleting {filepath}: {e}")
    
    def auto_delete_single_group(self, duplicates):
        """Auto-delete for a single group, keeping newest"""
        duplicates.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        file_to_keep = duplicates[0]
        
        print(f"Auto-keeping newest: {file_to_keep}")
        
        for filepath in duplicates[1:]:
            try:
                file_size = os.path.getsize(filepath)
                os.remove(filepath)
                self.total_size_freed += file_size
                self.files_deleted += 1
                print(f"✓ Deleted: {filepath} ({self.format_size(file_size)})")
            except OSError as e:
                print(f"✗ Error deleting {filepath}: {e}")
    
    def auto_delete_all(self):
        """Automatically delete all duplicates, keeping newest files"""
        if not self.duplicate_groups:
            print("No duplicates found to delete.")
            return
        
        print(f"\nAuto-deleting duplicates from {len(self.duplicate_groups)} groups...")
        print("Keeping newest files, deleting older duplicates...")
        
        for group_num, (file_hash, duplicates) in enumerate(self.duplicate_groups.items(), 1):
            print(f"\n--- Processing Group {group_num}/{len(self.duplicate_groups)} ---")
            self.auto_delete_single_group(duplicates)
    
    def show_final_summary(self):
        """Display comprehensive summary"""
        scan_mode = "Current directory and all subdirectories" if self.recursive else "Current directory only"
        
        print(f"\n{'='*80}")
        print("FINAL SUMMARY")
        print(f"{'='*80}")
        print(f"Scan mode:                {scan_mode}")
        print(f"Files processed:          {self.files_processed:,}")
        print(f"Duplicate groups found:   {len(self.duplicate_groups):,}")
        print(f"Total duplicate files:    {self.total_duplicate_files:,}")
        print(f"Files deleted:            {self.files_deleted:,}")
        print(f"Space freed:              {self.format_size(self.total_size_freed)}")
        
        # Calculate statistics
        if self.total_duplicate_files > 0:
            duplicate_percentage = (self.total_duplicate_files / self.files_processed) * 100
            print(f"Duplicate percentage:     {duplicate_percentage:.1f}%")
        
        # Show remaining files
        remaining_files = self.files_processed - self.files_deleted
        print(f"Remaining files:          {remaining_files:,}")
        
        print(f"{'='*80}")
        
        if self.files_deleted > 0:
            print("🎉 Cleanup completed successfully!")
        elif self.duplicate_groups:
            print("ℹ️  No files were deleted (skipped mode).")
        else:
            print("✅ No duplicate files found!")

def main():
    # Get current directory
    current_dir = os.getcwd()
    directories_to_scan = [current_dir]
    
    print("🔍 Duplicate File Finder")
    print("=" * 50)
    print(f"Current directory: {current_dir}")
    print("Algorithm: SHA-256")
    print("=" * 50)
    
    # Create finder instance (recursive mode will be set by user)
    finder = DuplicateFileFinder(directories=directories_to_scan, min_size=1024, recursive=True)
    
    try:
        # Step 1: Ask user about scan mode
        scan_mode = finder.ask_scan_mode()
        print(f"\nSelected scan mode: {scan_mode}")
        
        # Step 2: Find duplicates
        print("\nStep 1: Finding duplicates...")
        finder.find_duplicates()
        
        # Step 3: Show summary and ask for action
        if finder.display_duplicate_summary():
            action = finder.ask_user_action()
            
            if action == 'quit':
                print("Exiting program...")
                return
            elif action == 'skip':
                print("Skipping file deletion...")
            elif action == 'auto':
                print("\nStarting auto-delete mode...")
                finder.auto_delete_all()
            elif action == 'interactive':
                finder.interactive_delete()
        
        # Step 4: Show final summary
        finder.show_final_summary()
        
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
        finder.show_final_summary()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()