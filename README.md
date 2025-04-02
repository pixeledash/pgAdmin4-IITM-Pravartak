# Enhancement to pgAdmin 4

pgAdmin 4 is a web-based administration and management tool for PostgreSQL databases. It is the latest version of pgAdmin, redesigned from earlier desktop-based versions to provide a modern, flexible, and user-friendly interface for managing PostgreSQL servers.

## Implemented Features  

#### **1. Automated Backup Scheduler**  
- **Flexible Scheduling Options** – Supports **one-time, daily, weekly, and monthly** backup schedules.  
- **Dynamic Scheduling Logic** – Automatically determines the next backup execution time based on prior runs.  
- **Background Scheduler Service** – Operates as a separate thread to manage backup jobs efficiently without interfering with pgAdmin4 operations.  
- **Job Management & Validation** – Ensures accurate backup job configurations using **SQLAlchemy**.  
- **API Endpoints** – Provides **REST API endpoints** for scheduling status monitoring and restarting the scheduler.  

#### **2. ERD Export Tool Enhancements**  
- **Multi-Format Export Support** – Enables **PNG, JPEG, WebP, and PDF** export options.  
- **High-Resolution Export** – Allows users to generate **2x resolution** images for better clarity.  
- **Quality Control for Image Formats** – Adjustable compression settings for **JPEG and WebP** exports.  
- **Automatic Sizing** – Dynamically determines diagram dimensions to **ensure all elements are captured**.  
- **Consistent Background Rendering** – Ensures a **uniform white background** for exported images.  
- **PDF Generation** – Leverages **jsPDF** to convert ERD diagrams into properly formatted **PDF documents**.  

#### **3. Schema Diff Tool Enhancements**  
- **Color-Coded SQL Differences** –  
  - **Additions** → Highlighted in Green  
  - **Deletions** → Highlighted in Red  
  - **Modifications** → Highlighted in Yellow  
- **Copy-to-Clipboard Functionality** – Enables efficient copying of SQL differences for quick reference.  
- **PropTypes Validation** – Ensures proper data handling within **React components**.  
- **UI/UX Enhancements** – Improved layout and styling for better readability.  

## Installation

### Building the Runtime

To build the runtime, the following packages must be installed:

* NodeJS 16+
* Yarn

Change into the runtime directory, and run *yarn install*. This will install the
dependencies required.

In order to use the runtime in a development environment, you'll need to copy
*dev_config.json.in* file to *dev_config.json*, and edit the paths to the Python
executable and *pgAdmin.py* file, otherwise the runtime will use the default
paths it would expect to find in the standard package for your platform.

You can then execute the runtime by running something like:

```bash
yarn run start
```

### Configuring the Python Environment

In order to run the Python code, a suitable runtime environment is required.
Python version 3.7 and later are currently supported. It is recommended that a
Python Virtual Environment is setup for this purpose, rather than using the
system Python environment. On Linux and Mac systems, the process is fairly
simple - adapt as required for your distribution:

1. Create a virtual environment in an appropriate directory. The last argument is
   the name of the environment; that can be changed as desired:

   ```bash
   $ python3 -m venv venv
   ```

2. Now activate the virtual environment:

   ```bash
   $ source venv/bin/activate
   ```

3. Some of the components used by pgAdmin require a very recent version of *pip*,
   so update that to the latest:

   ```bash
   $ pip install --upgrade pip
   ```

4. Ensure that a PostgreSQL installation's bin/ directory is in the path (so
   pg_config can be found for building psycopg3), and install the required
   packages:

   ```bash
   (venv) $ PATH=$PATH:/usr/local/pgsql/bin pip install -r $PGADMIN4_SRC/requirements.txt
   ```

   If you are planning to run the regression tests, you also need to install
   additional requirements from web/regression/requirements.txt:

   ```bash
   (venv) $ pip install -r $PGADMIN4_SRC/web/regression/requirements.txt
   ```

5. Create a local configuration file for pgAdmin. Edit
   $PGADMIN4_SRC/web/config_local.py and add any desired configuration options
   (use the config.py file as a reference - any settings duplicated in
   config_local.py will override those in config.py). A typical development
   configuration may look like:

    ```python
    from config import *

    # Debug mode
    DEBUG = True

    # App mode
    SERVER_MODE = True

    # Enable the test module
    MODULE_BLACKLIST.remove('test')

    # Log
    CONSOLE_LOG_LEVEL = DEBUG
    FILE_LOG_LEVEL = DEBUG

    DEFAULT_SERVER = '127.0.0.1'

    UPGRADE_CHECK_ENABLED = True

    # Use a different config DB for each server mode.
    if SERVER_MODE == False:
        SQLITE_PATH = os.path.join(
            DATA_DIR,
            'pgadmin4-desktop.db'
        )
    else:
        SQLITE_PATH = os.path.join(
            DATA_DIR,
            'pgadmin4-server.db'
        )
   ```

   This configuration allows easy switching between server and desktop modes
   for testing.

6. The initial setup of the configuration database is interactive in server
   mode, and non-interactive in desktop mode. You can run it either by
   running:

   ```bash
   (venv) $ python3 $PGADMIN4_SRC/web/setup.py
   ```

   or by starting pgAdmin 4:

   ```bash
   (venv) $ python3 $PGADMIN4_SRC/web/pgAdmin4.py
   ```

   Whilst it is possible to automatically run setup in desktop mode by running
   the runtime, that will not work in server mode as the runtime doesn't allow
   command line interaction with the setup program.

At this point you will be able to run pgAdmin 4 from the command line in either
server or desktop mode, and access it from a web browser using the URL shown in
the terminal once pgAdmin has started up.

Setup of an environment on Windows is somewhat more complicated unfortunately,
please see *pkg/win32/README.txt* for complete details.

### Building the Web Assets

pgAdmin is dependent on a number of third party Javascript libraries. These,
along with it's own Javascript code, SCSS/CSS code and images must be
compiled into a "bundle" which is transferred to the browser for execution
and rendering. This is far more efficient than simply requesting each
asset as it's needed by the client.

To create the bundle, you will need the 'yarn' package management tool to be
installed. Then, you can run the following commands on a *nix system to
download the required packages and build the bundle:

```bash
(venv) $ cd $PGADMIN4_SRC
(venv) $ make install-node
(venv) $ make bundle
```

On Windows systems (where "make" is not available), the following commands
can be used:

```
C:\> cd $PGADMIN4_SRC\web
C:\$PGADMIN4_SRC\web> yarn install
C:\$PGADMIN4_SRC\web> yarn run bundle
```

### Building packages

Most packages can be built using the Makefile in $PGADMIN4_SRC, provided all
the setup and configuration above has been completed.

To build a source tarball:

```bash
(venv) $ make src
```

To build a PIP Wheel, activate either a Python 3 virtual environment, configured
with all the required packages, and then run:

```bash
(venv) $ make pip
```

To build the macOS AppBundle, please see *pkg/mac/README*.

To build the Windows installer, please see *pkg/win32/README.txt*.
### Create Database Migrations

In order to make changes to the SQLite DB, navigate to the 'web' directory:

```bash
(venv) $ cd $PGADMIN4_SRC/web
```

Create a migration file with the following command:

```bash
(venv) $ FLASK_APP=pgAdmin4.py flask db revision
```

This will create a file in: $PGADMIN4_SRC/web/migrations/versions/ .
Add any changes to the 'upgrade' function.
Increment the SCHEMA_VERSION in $PGADMIN4_SRC/web/pgadmin/model/__init__.py file.

There is no need to increment the SETTINGS_SCHEMA_VERSION.

# Implementation

## Automated Backup Scheduler Implementation

### Overview

The pgAdmin 4 Automated Backup Scheduler provides a robust system for scheduling and executing database backups. This implementation allows administrators to configure recurring backups with minimal intervention.

### Flexible Scheduling Options

The scheduler supports multiple backup frequencies through a comprehensive scheduling system:

1. **One-time Backups**: Executes a single backup at a specified date and time, ideal for pre-maintenance backups
2. **Daily Backups**: Runs backups every day at the configured time, perfect for daily snapshots
3. **Weekly Backups**: Allows selection of specific days of the week for backups, useful for end-of-week archives
4. **Monthly Backups**: Enables backups on chosen months, suitable for long-term retention policies

The UI presents these options through an intuitive form with appropriate date/time selectors and repeat interval choices.

### Dynamic Scheduling Logic

The scheduler implements intelligent timing calculations through several key features:

1. **Next Run Calculator**: Automatically determines the next execution time based on:
   - The schedule type (one-time, daily, weekly, monthly)
   - Previous execution time
   - Configured intervals and preferences

2. **Schedule Validation**: Ensures valid scheduling by:
   - Preventing past dates/times
   - Validating month/day combinations
   - Handling timezone considerations

3. **Run-time Adjustments**: Manages edge cases like:
   - Month transitions with varying days
   - Daylight saving time changes
   - Leap year considerations

### Background Scheduler Service

The service operates independently through a robust background process:

1. **Thread Management**:
   - Runs as a daemon thread
   - Maintains its own lifecycle
   - Handles graceful shutdown

2. **Error Recovery**:
   - Implements retry mechanisms
   - Logs failures for troubleshooting
   - Maintains scheduler state during issues

3. **Resource Optimization**:
   - Uses efficient sleep/wake cycles
   - Minimizes database connections
   - Optimizes memory usage

### Job Management & Validation

Comprehensive job handling system includes:

1. **Data Storage**:
   - Uses SQLAlchemy ORM for job persistence
   - Maintains job history and status
   - Tracks execution statistics

2. **Configuration Validation**:
   - Validates required parameters
   - Checks file paths and permissions
   - Verifies database connectivity

3. **Status Tracking**:
   - Monitors job execution
   - Records success/failure states
   - Maintains execution logs

### API Endpoints

The scheduler exposes RESTful endpoints for control and monitoring:

1. **Status Endpoints**:
   - Get scheduler status
   - List active jobs
   - View job history

2. **Control Endpoints**:
   - Start/stop scheduler
   - Add/remove jobs
   - Modify schedules

3. **Monitoring Endpoints**:
   - Health checks
   - Performance metrics
   - Error reporting


### Screenshots
#### Backup Dialog UI 
![Backup Dialog 1](img/backup%20ui%201.png)
![Backup Dialog 2](img/backup%20ui%202.png)

#### Working

1.Backup Scheduled
![Backup Log 1](img/backup%20log%201.png)

2.Thread checking for jobs every 30 sec
![Backup Log 2](img/backup%20log%202.png)

3.Job creation
![Backup Log 3](img/backup%20log%203.png)

4.Process in pgAdmin UI
![Backup Dialog 3](img/backup%20ui%203.png)


## ERD Tool Implementation

### Overview

The Entity Relationship Diagram (ERD) tool in pgAdmin 4 includes a comprehensive export system supporting multiple image formats and PDF output. This implementation enables users to capture, share, and document their database designs with high-quality visuals.

### Multi-Format Export Support
The ERD tool provides comprehensive export capabilities supporting multiple formats through a user-friendly dialog interface. Users can choose between:
- PNG format for lossless quality and transparency
- JPEG format with adjustable compression for smaller file sizes
- WebP format for modern web-optimized images
- PDF format for professional documentation

The format selection is implemented using Material-UI's Select component, which triggers format-specific processing logic when an export is initiated.

### High-Resolution Export
To support high-quality exports, especially for large displays or printing:
- A checkbox option enables 2x resolution export
- When enabled, the export dimensions are doubled
- The high-resolution option works across all supported formats
- Image quality is maintained through proper scaling algorithms
- Particularly useful for detailed diagrams or presentations

### Quality Control for Image Formats
For formats supporting compression (JPEG and WebP):
- A quality slider appears dynamically when these formats are selected
- Quality range from 10-100 allows fine-tuned control
- Lower values reduce file size but may affect image quality
- Higher values maintain quality but increase file size
- The slider provides immediate visual feedback

### Automatic Sizing
The export system implements intelligent dimension calculation:
1. Analyzes all diagram elements including nodes and links
2. Determines the bounding box of the entire diagram
3. Adds appropriate margins to prevent content cropping
4. Handles both compact and expansive diagrams
5. Ensures no diagram elements are cut off in the export

### Consistent Background Rendering
To ensure professional-looking exports:
- Enforces a clean white background for all exports
- Temporarily overrides any custom background settings
- Preserves the original diagram styling during export
- Restores all original styles after export completion
- Maintains consistency across different export formats

### PDF Generation
The PDF export process involves several sophisticated steps:
1. Initial conversion to high-quality PNG
2. Intelligent orientation selection (portrait/landscape)
3. Proper scaling to fit standard PDF dimensions
4. Preservation of diagram clarity and readability
5. Integration with jsPDF for reliable PDF generation

### Error Handling
Robust error handling ensures reliability:
- Validates export parameters before processing
- Provides meaningful error messages
- Handles memory constraints gracefully
- Recovers from failed export attempts
- Maintains diagram state integrity

### Usage Example

The export functionality is triggered from the ERD toolbar:

```javascript
<PgIconButton 
  title={gettext('Export Diagram')} 
  icon={<FileDownloadRoundedIcon />}
  shortcut={preferences.export_diagram}
  onClick={() => {
    eventBus.fireEvent(ERD_EVENTS.SHOW_EXPORT_DIALOG);
  }} 
/>
```
Export tool in Main tool bar

![ERD 1](img/erd%201.png)

PNG features

![ERD 2](img/erd%202.png)

JPEG,WebP features

![ERD 3](img/erd%203.png)

Export formats

![ERD 4](img/erd%204.png)


### Results Comparison

| Format | File Size | Resolution | Quality | Notes |
|--------|-----------|------------|---------|-------|
| PNG    | 45-120KB  | Original   | Lossless| Best for diagrams with text |
| PNG 2x | 120-250KB | 2x         | Lossless| Sharper text, larger file |
| JPEG   | 25-80KB   | Original   | 90%     | Smallest file size, some artifacts |
| WebP   | 30-90KB   | Original   | 90%     | Good balance of quality and size |
| PDF    | 100-200KB | Original   | -       | Best for printing and documents |


## Schema Diff Tool Implementation

### Color-Coded SQL Differences

The Schema Diff tool implements a sophisticated color-coding system to help users quickly identify different types of SQL changes:

The core functionality is provided by the `parseAndColorCodeDiff` utility function that processes SQL text and applies appropriate CSS classes. It identifies three types of changes:

- **Additions** (green) - Identified by keywords like CREATE, INSERT, ADD, or lines starting with "+"
- **Deletions** (red) - Identified by keywords like DROP, DELETE, REMOVE, or lines starting with "-"
- **Modifications** (yellow) - Identified by keywords like ALTER, UPDATE, MODIFY

The CSS styling for these highlights is defined in the theme's CodeMirror overrides:

```
'.diff-added' → backgroundColor: 'rgba(0, 155, 0, 0.2)', color: '#006400'
'.diff-removed' → backgroundColor: 'rgba(255, 0, 0, 0.2)', color: '#8B0000'
'.diff-modified' → backgroundColor: 'rgba(255, 204, 0, 0.2)', color: '#806600'
```

![Schema 2](img/schema%202.png)

### Copy-to-Clipboard Functionality

A dedicated `CopyButton` component is implemented for the SQL diff section that:

1. Shows a copy icon in the top-right corner of the SQL diff container
2. Uses the `copyToClipboard` utility to copy the raw SQL text
3. Provides visual feedback by temporarily changing to a checkmark icon after copying
4. Reverts back to the copy icon after a delay using a custom hook (`useDelayedCaller`)

This implementation helps users easily capture the SQL differences for sharing or applying to their databases.

![Copy](img/schema%203.png)

### PropTypes Validation

The Schema Diff components use React's PropTypes system to ensure proper data typing:

- The `CopyButton` component validates that the `text` prop is a required string
- The `Results` component includes PropTypes validation for its props
- This validation helps prevent errors during development and provides better documentation

### UI/UX Enhancements

The Schema Diff results display features several UI enhancements:

1. **Three-column layout** that shows Source, Target and Difference side by side
2. **Fixed headers** with clear section labels for better orientation
3. **Monospace font** for SQL content to maintain proper code formatting
4. **Scrollable containers** that handle overflow content while maintaining layout
5. **Consistent styling** that follows the application's theme (light/dark mode compatible)

The component uses a styled container with CSS classes that create a responsive layout. The SQL diff section specifically uses a custom container rather than the standard SQL editor component to enable the color-coded highlighting.

When SQL differences are detected, the component processes the diff text through the highlighter utility and renders it using `dangerouslySetInnerHTML` to preserve the HTML color formatting, while ensuring clipboard functionality still works with the plain text version.

This comprehensive approach creates a visually intuitive interface that helps database administrators easily identify and understand schema differences between databases or database objects.


![Schema 1](img/schema%201.png)

In dark mode

![Schema 4](img/schema%204.png)

In high contrast mode

![Schema 3](img/schema%205.png)


## Running pgAdmin4
### In server mode
```bash
(venv) $ cd $PGADMIN4_SRC/web
(venv) $ python3 pgAdmin4.py
```
### In desktop runtime
```bash
(venv) $ cd $PGADMIN4_SRC/runtime
(venv) $ yarn run start
```

## Additional Resources

- General documentation: https://www.pgadmin.org/docs
- Latest versions: https://www.pgadmin.org/download/
- Main website: https://www.pgadmin.org/
- Copyright and license information can be found in the file LICENCE.
  
## Contributors
- Niyati Pradeep(https://github.com/niyatipradeep)
- Ashmal Faisal(https://github.com/pixeledash)
- Nanda Kishor (https://github.com/anikkilnandakishor)




