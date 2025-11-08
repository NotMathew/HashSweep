**📋 Description**

A powerful Python script that identifies and manages duplicate files across your system using SHA-256 hashing for accurate detection. It helps you reclaim valuable disk space by safely removing redundant files while giving you full control over the deletion process.

**🎯 Key Features**

- **Smart Detection:** Uses SHA-256 cryptographic hashing to ensure 100% accurate duplicate identification  
- **Multiple Scan Modes:** Choose between current directory only or recursive scanning through all subdirectories  
- **Safe Management:** Three operation modes for maximum control:  
  - **Interactive Mode:** Manually choose which duplicates to keep/delete for each file group  
  - **Auto-Delete Mode:** Automatically keeps newest files and deletes older duplicates  
  - **Skip Mode:** Just identify duplicates without deleting anything  
- **Comprehensive Summary:** Detailed report showing space recovered, files processed, and statistics  
- **Performance Optimized:** First filters by file size, then verifies with hashing for speed  
- **User-Friendly:** Clear prompts and progress indicators throughout the process 

**📁 Supported Platforms**

- Windows
- Linux
- macOS

**📦 Dependencies**

    None! Uses only Python standard library modules

## Installation on Windows 10/11
Go to [Releases](https://github.com/NotMathew/HashSweep/releases) and download the lastest version.

## Installation on Linux

```
git clone https://github.com/NotMathew/HashSweep.git
cd HashSweep
python HashSweep.py
```






