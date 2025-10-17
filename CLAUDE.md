# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Babelcomics4 is a GTK4/libadwaita comic collection manager written in Python. It provides a modern interface for organizing digital comics (CBR, CBZ, PDF) with database-backed metadata, thumbnail generation, and ComicVine API integration.

## Development Commands

### Setup and Installation
```bash
# Initial setup (creates directories, installs dependencies, configures database)
python3 setup.py

# Install Python dependencies
pip3 install -r requirements.txt

# Run the application
python3 Babelcomic4.py
# OR use the convenience script
./babelcomics4.sh
```

### System Dependencies
The application requires GTK4 and libadwaita system packages:
```bash
# Ubuntu/Debian
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1

# Arch Linux
sudo pacman -S python-gobject gtk4 libadwaita

# Fedora
sudo dnf install python3-gobject gtk4-devel libadwaita-devel
```

## Architecture Overview

### Core Structure
- **Main Application**: `Babelcomic4.py` - Entry point and main window
- **Entity Models**: `entidades/` - SQLAlchemy database models
- **Repositories**: `repositories/` - Data access layer with both standard and GTK4 variants
- **UI Components**: Modular widgets for cards, dialogs, and detail views
- **Helpers**: `helpers/` - Utility modules for scanning, extraction, ComicVine API

### Database Architecture
- **SQLite database**: `data/babelcomics.db`
- **Main entities**: Comicbook, Volume, Publisher, ComicbookInfo, Setup
- **Thumbnail storage**: `data/thumbnails/` with subdirectories for each entity type
- **ORM**: SQLAlchemy 2.0+ with declarative base in `entidades/__init__.py`

### Key Components

#### Entity Models (`entidades/`)
- `comicbook_model.py` - Physical comic files
- `volume_model.py` - Series/volume information
- `publisher_model.py` - Publisher data
- `comicbook_info_model.py` - Comic metadata from ComicVine (with ComicVine ID storage)
- `comicbook_info_cover_model.py` - Multiple cover support for ComicbookInfo
- `setup_model.py` - Application configuration

#### Repositories (`repositories/`)
- Follow repository pattern with base classes
- GTK4-specific variants (`*_gtk4.py`) for UI integration
- Handle database operations and provide data to UI components

#### UI Modules
- `comic_cards.py` - Card widgets for grid displays with multiselection support
- `filter_dialog.py` - Advanced search and filtering
- `comic_detail_page.py` - Detailed comic information view
- `volume_detail_page.py` - Volume/series details with ComicbookInfo detail pages
- `physical_comics_page.py` - Physical comics view with navigation from ComicbookInfo
- `selectable_card.py` - Base selectable card with selection manager (Ctrl+A support)
- `thumbnail_generator.py` - Image processing and thumbnail creation

#### Helper Modules (`helpers/`)
- `comic_scanner.py` - Directory scanning for comic files
- `comic_extractor.py` - Comic file extraction (CBZ/CBR/CB7)
- `comicvine_cliente.py` - ComicVine API integration
- `config_helper.py` - Configuration management

### Data Flow
1. **Scanning**: `comic_scanner.py` finds comic files in configured directories
2. **Database**: Files are stored as Comicbook entities via repositories
3. **Thumbnails**: `thumbnail_generator.py` creates preview images
4. **UI Display**: Card widgets show comics in grid layouts
5. **Detail Views**: Pages show comprehensive information and extracted pages
6. **Metadata**: ComicVine integration enriches comic information

### Configuration
- **Setup data**: Stored in `setup` and `setup_directorio` database tables
- **Scan directories**: Configured through setup system
- **Thumbnails**: Generated on-demand and cached in `data/thumbnails/`

## Development Notes

### Module Dependencies
- The application checks for ComicbookInfo import and gracefully degrades if unavailable
- Repository classes have both standard and GTK4 variants for different use cases
- Thumbnail generation handles multiple image formats and comic archive types

### Search System
- Advanced filtering implemented in `filter_dialog.py`
- Context-specific search (independent for Comics, Volumes, Publishers)
- Multi-term search with '+' operator support
- Example: `Superman+2015` finds comics containing both terms

### File Format Support
- **CBZ/ZIP**: Primary format, direct ZIP handling
- **CBR/RAR**: Requires `unrar` command-line tool
- **CB7/7Z**: Requires `7z` command-line tool
- **PDF**: Basic support for metadata extraction

### Testing
No formal test framework is currently configured. Manual testing is done through the GUI.

## Recent Features Added

### Multiselection Enhancements
- **Ctrl+A Support**: Select all items in grid views (comics, volumes, publishers)
- **Context Menu Integration**: Unified context menu works with both single and multiple selections
- **Bulk Operations**: Trash and catalog operations support multiple items efficiently

#### Implementation Details:
```python
# Unified approach for single/multiple operations
def move_items_to_trash(self, item_ids):
    """Handle single ID or list of IDs"""
    if not isinstance(item_ids, list):
        item_ids = [item_ids]
    # Process all IDs uniformly
```

### ComicVine Data Enhancement
- **ComicVine ID Storage**: All ComicbookInfo records now store ComicVine IDs
- **URL Preservation**: API and site URLs stored for future reference
- **Multiple Covers**: Support for downloading and displaying variant covers

#### Database Schema Updates:
```sql
-- ComicbookInfo table enhanced with:
comicvine_id INTEGER DEFAULT 0
url_api_detalle VARCHAR  -- ComicVine API URL
url_sitio_web VARCHAR    -- ComicVine site URL
```

### UI/UX Improvements
- **ComicbookInfo Detail Pages**: Dedicated detail view for comic metadata
- **Cover Carousel**: Multiple cover display using Adw.Carousel
- **Physical Comics Navigation**: Seamless navigation from metadata to physical files
- **Robust Image Loading**: Enhanced file search with glob patterns for cover variants

#### Navigation Flow:
```
Volume Details → ComicbookInfo Details → Physical Comics View
```

### File Management Enhancements
- **Variant Cover Support**: Handles filename variations (e.g., `cover_variant_1.jpg`)
- **Fallback Mechanisms**: Graceful degradation when covers aren't found
- **Efficient Caching**: Thumbnail caching for improved performance

## Recent Bug Fixes

### ComicVine Data Update Issues
**Problem**: ComicVine IDs and URLs weren't being saved during volume updates due to duplicate function implementations.

**Root Cause**: Two separate sets of update functions existed:
- `repositories/volume_repository.py`: `_update_existing_issue()` (correct implementation)
- `volume_detail_page.py`: `update_existing_issue()` (incomplete implementation)

**Solution**: Fixed both function sets to ensure ComicVine data is always updated:
```python
# Now both functions properly update ComicVine fields
existing_issue.comicvine_id = issue_data['id']
existing_issue.url_api_detalle = issue_data['api_detail_url']
existing_issue.url_sitio_web = issue_data['site_detail_url']
```

### Image Loading Robustness
**Problem**: Cover images weren't loading due to filename mismatches between database records and downloaded files.

**Solution**: Implemented robust file search with glob patterns:
```python
possible_patterns = [
    f"data/thumbnails/comicbook_info/*/{filename}",          # Exact match
    f"data/thumbnails/comicbook_info/*/{base_name}_variant_*.{extension}",  # Variants
    f"data/thumbnails/comicbook_info/*/{base_name}.{extension}",            # Without variant
]
```

## Common Tasks

### Adding New Entity Types
1. Create model in `entidades/`
2. Create repository in `repositories/`
3. Add to imports in `entidades/__init__.py`
4. Update database schema migration if needed

### Modifying UI Components
- Card widgets follow the pattern in `comic_cards.py`
- Use `SelectableCard` base class for grid items
- Detail pages follow `comic_detail_page.py` pattern

### ComicVine Integration
- API client in `helpers/comicvine_cliente.py`
- Download window: `comicvine_download_window.py`
- Metadata models: `comicbook_info_model.py` and related
- **Enhanced Features**:
  - ComicVine ID storage in ComicbookInfo records
  - Multiple cover download and storage (main + associated_images)
  - Robust cover file loading with fallback mechanisms
  - API and site URL storage for future reference

## ⚠️ Known Architectural Issues

### Database Access Violations
**CRITICAL**: The codebase currently violates separation of concerns by having UI components directly access the database. This creates tight coupling and maintenance issues.

#### Current Violations:
- **`Babelcomic4.py`**: Main window directly uses `session.query()` and `session.commit()`
  - Lines 738-750: Direct SQLAlchemy queries in UI event handlers
  - Lines 854-857, 876: Database operations in UI methods
  - Lines 1126-1133: Statistics queries in UI update methods

- **`volume_detail_page.py`**: UI page with extensive database access
  - Multiple `session.query()` calls for counts, publisher lookup, comic info queries
  - Direct `session.add()` and `session.commit()` operations
  - SQLAlchemy imports and complex queries in UI functions

- **`comic_cards.py`**: Card widgets performing database queries
  - Direct session usage for counting owned comics and volumes
  - SQLAlchemy queries in UI component initialization

#### Correct Architecture Pattern:
```python
# ❌ WRONG: UI doing direct database access
comic = self.session.query(Comicbook).get(item_id)
comic.en_papelera = True
self.session.commit()

# ✅ CORRECT: UI using repository methods
self.comic_repository.move_to_trash(item_id)
```

#### Required Refactoring:
1. **Move all database operations to repositories**
2. **Create service layer for complex business logic**
3. **UI should only call repository/service methods**
4. **Remove SQLAlchemy imports from UI modules**

### Recommended Service Layer
Create service classes for complex operations:
```python
# services/comic_service.py
class ComicService:
    def __init__(self, comic_repo, volume_repo):
        self.comic_repo = comic_repo
        self.volume_repo = volume_repo

    def get_collection_stats(self):
        return {
            'comics': self.comic_repo.count_all(),
            'volumes': self.volume_repo.count_all()
        }

    def move_comics_to_trash(self, comic_ids):
        return self.comic_repo.move_multiple_to_trash(comic_ids)
```

### Repository Enhancement Needed
Current repositories need methods for UI operations:
- ✅ `move_to_trash(item_id)` - **IMPLEMENTED**
- ✅ `move_multiple_to_trash(item_ids)` - **IMPLEMENTED** as `move_items_to_trash()`
- `get_collection_stats()`
- `count_by_criteria(filters)`

### Recent Architecture Improvements
- **Unified Trash Operations**: Implemented `move_items_to_trash()` that handles both single IDs and lists
- **ComicVine Data Consistency**: Fixed duplicate function implementations causing data inconsistency
- **Robust File Loading**: Improved file search mechanisms reducing UI-level file system access