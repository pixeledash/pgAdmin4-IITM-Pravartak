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

The scheduler supports multiple backup frequencies:

```python
class BackupSchedulerJob:
    def __init__(self, sid, data, schedule_type, start_time):
        self.schedule_type = schedule_type  # 'one_time', 'daily', 'weekly', or 'monthly'
        self.start_time = start_time
        # ...
```

Users can select from various schedule types through the UI:

```javascript
// UI scheduling options
<Select value={schedule_type}>
  <MenuItem value="one_time">{gettext('One time')}</MenuItem>
  <MenuItem value="daily">{gettext('Daily')}</MenuItem>
  <MenuItem value="weekly">{gettext('Weekly')}</MenuItem>
  <MenuItem value="monthly">{gettext('Monthly')}</MenuItem>
</Select>
```

For weekly and monthly schedules, additional options allow specific day/month selection.

### Dynamic Scheduling Logic

The scheduler calculates the next execution time based on schedule type:

```python
def calculate_next_run(self):
    """Calculate the next run time based on schedule type"""
    if self.schedule_type == 'daily':
        self.next_run = self.last_run.replace(
            hour=self.start_time.hour,
            minute=self.start_time.minute
        ) + timedelta(days=1)
    elif self.schedule_type == 'weekly':
        # Weekly logic
    elif self.schedule_type == 'monthly':
        # Monthly logic with proper month transition handling
```

### Background Scheduler Service

The scheduler operates as a separate thread to avoid interfering with main application operations:

```python
def start(self):
    """Start the scheduler thread"""
    self.running = True
    self.thread = threading.Thread(target=self._run, name="BackupScheduler")
    self.thread.daemon = False
    self.thread.start()
```

The main scheduler loop continuously checks for jobs to execute:

```python
def _run(self):
    """Main scheduler loop"""
    while self.running:
        with self.app.app_context():
            for sid, job_list in self.jobs.items():
                for job in job_list:
                    if job.should_run():
                        self._execute_backup(job)
                        job.last_run = datetime.now()
                        job.calculate_next_run()
        time.sleep(30)  # Check every 30 seconds
```

### Job Management & Validation

Backup jobs are stored using SQLAlchemy ORM:

```python
class BackupSchedule(Base):
    """ORM model for backup schedule configurations"""
    __tablename__ = 'backup_schedules'
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, nullable=False)
    file_directory = Column(String, nullable=False)
    backup_frequency = Column(String, nullable=False)
    # Additional fields...
```

Configuration validation ensures valid parameters:

```python
def _validate_backup_config(self, config):
    """Validate backup configuration"""
    # Check required fields
    # Validate time format
    # Ensure proper schedule configuration
```

### API Endpoints

RESTful API endpoints enable monitoring and management:

```python
@blueprint.route('/scheduler_status', methods=['GET'])
@pga_login_required
def scheduler_status():
    """Return scheduler status information"""
    status_data = {
        'running': backup_scheduler.running,
        'job_count': sum(len(jobs) for jobs in backup_scheduler.jobs.values()),
        'jobs': {}  # Populate with job details
    }
    return make_json_response(data=status_data)

@blueprint.route('/restart_scheduler', methods=['POST'])
@pga_login_required
def restart_scheduler():
    """Restart the backup scheduler service"""
    if backup_scheduler.running:
        backup_scheduler.stop()
    backup_scheduler.start()
    return make_json_response(data={'success': True})
```

### Execution Process

When a backup job runs, the system establishes a database connection and executes the backup using the same utilities as manual backups:

```python
def _execute_backup(self, job):
    """Execute a backup job"""
    with self.app.test_request_context():
        # Set up authentication context
        # Connect to server
        # Configure backup parameters
        # Execute backup process
        # Record results
```
### Screenshots
![Backup Dialog 1]("img/backup%20ui%201.png")
![Backup Dialog 2]("img/backup%20ui%202.png")
![Backup Log 1]("img/backup%20log%201.png")
![Backup Log 2]("img/backup%20log%202.png")
![Backup Log 3]("img/backup%20log%203.png")
![Backup Dialog 3]("img/backup%20ui%203.png")


## Multi-Format ERD Export Implementation

### Overview

The Entity Relationship Diagram (ERD) tool in pgAdmin 4 includes a comprehensive export system supporting multiple image formats and PDF output. This implementation enables users to capture, share, and document their database designs with high-quality visuals.

### Multi-Format Export Support

The export dialog provides users with multiple output format options:

```javascript
<FormControl fullWidth>
  <InputLabel>{gettext('Export Format')}</InputLabel>
  <Select
    value={format}
    onChange={(e) => setFormat(e.target.value)}
  >
    <MenuItem value="png">PNG</MenuItem>
    <MenuItem value="jpeg">JPEG</MenuItem>
    <MenuItem value="webp">WebP</MenuItem>
    <MenuItem value="pdf">PDF</MenuItem>
  </Select>
</FormControl>
```

Each format is processed with format-specific optimization:

```javascript
switch (format) {
  case 'jpeg':
    exportPromise = domtoimage.toJpeg(this.canvasEle, exportOptions);
    break;
  case 'webp':
    // Custom WebP conversion with quality control
    exportPromise = domtoimage.toPng(this.canvasEle)
      .then(pngDataUrl => {
        return new Promise((resolve) => {
          const img = new Image();
          img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);
            const webpDataUrl = canvas.toDataURL('image/webp', 
              options.quality ? options.quality / 100 : undefined);
            resolve(webpDataUrl);
          };
          img.src = pngDataUrl;
        });
      });
    break;
  // Additional formats...
}
```

### High-Resolution Export

Users can enable 2x resolution for sharper images:

```javascript
<FormControlLabel
  control={
    <Checkbox 
      checked={highResolution} 
      onChange={(e) => setHighResolution(e.target.checked)} 
    />
  }
  label={gettext('High resolution (2x)')}
/>
```

Implementation scales dimensions proportionally:

```javascript
// Apply high resolution scaling
const scale = options.highResolution ? 2 : 1;
if (options.highResolution) {
  width *= scale;
  height *= scale;
}
```

### Quality Control for Lossy Formats

For JPEG and WebP formats, a quality slider is provided:

```javascript
{showQualityOption && (
  <Box sx={{ mb: 2 }}>
    <Typography id="quality-slider" gutterBottom>
      {gettext('Quality')}
    </Typography>
    <Slider
      value={quality}
      onChange={(e, newValue) => setQuality(newValue)}
      valueLabelDisplay="auto"
      min={10}
      max={100}
    />
  </Box>
)}
```

The quality value is applied during export:

```javascript
const exportOptions = {
  width,
  height,
  quality: options.quality ? options.quality / 100 : undefined,
  bgcolor: '#ffffff',
};
```

### Automatic Sizing and Positioning

The export process automatically calculates the dimensions required to include all diagram elements:

```javascript
// Calculate content dimensions including all elements
const contentWidth = Math.max(
  linksRect.BR.x - linksRect.TL.x,
  nodesRect.getBottomRight().x - nodesRect.getTopLeft().x
);
const contentHeight = Math.max(
  linksRect.BR.y - linksRect.TL.y,
  nodesRect.getBottomRight().y - nodesRect.getTopLeft().y
);

// Check what is to the most top left - links or nodes?
let topLeftXY = {
  x: Math.min(nodesRect.getTopLeft().x, linksRect.TL.x),
  y: Math.min(nodesRect.getTopLeft().y, linksRect.TL.y)
};
topLeftXY.x -= margin;
topLeftXY.y -= margin;
```

The diagram is then repositioned to ensure complete capture:

```javascript
// Transform the diagram to capture all content
this.canvasEle.childNodes.forEach((ele) => {
  ele.style.transform = `translate(${nodeLayerTopLeftPoint.x - nodesRectTopLeftPoint.x}px, 
    ${nodeLayerTopLeftPoint.y - nodesRectTopLeftPoint.y}px) scale(1.0)`;
});
```

### PDF Generation

PDF export uses a two-step process:

1. First converting the diagram to a PNG image
2. Then creating a properly formatted PDF with jsPDF

```javascript
if (format === 'pdf') {
  import('dom-to-image-more').then((domtoimage) => {
    domtoimage.toPng(this.canvasEle, exportOptions)
      .then((dataUrl) => {
        import('jspdf').then(({ jsPDF }) => {
          const pdf = new jsPDF({
            orientation: width > height ? 'landscape' : 'portrait',
            unit: 'px',
            format: [width, height]
          });
          const imgProps = pdf.getImageProperties(dataUrl);
          const pdfWidth = pdf.internal.pageSize.getWidth();
          const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
          pdf.addImage(dataUrl, 'PNG', 0, 0, pdfWidth, pdfHeight);
          pdf.save(fileName + '.pdf');
        });
      });
  });
}
```

### Performance Optimization

The implementation includes several optimizations to ensure high-quality exports:

1. **State Preservation**: Original styles are saved and restored after export:
   ```javascript
   // Save original styles before modifying
   const originalStyles = {
     width: this.canvasEle.style.width,
     height: this.canvasEle.style.height,
     background: this.canvasEle.style.background,
     canvasBgImage: this.canvasEle.style.backgroundImage
   };
   
   // Later restore these styles
   restoreOriginalStyles(prevTransform, originalStyles, containerOriginalBg);
   ```

2. **Size Limitation Handling**: Large diagrams are automatically scaled to fit maximum allowed dimensions:
   ```javascript
   if(width >= 32767) {
     width = 32766;
     isCut = true;
   }
   if(height >= 32767) {
     height = 32766;
     isCut = true;
   }
   ```

3. **Consistent Rendering**: Background grid is temporarily removed to ensure clean exports:
   ```javascript
   this.diagramContainerRef.current?.classList.add('ERDTool-html2canvasReset');
   ```

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

### Copy-to-Clipboard Functionality

A dedicated `CopyButton` component is implemented for the SQL diff section that:

1. Shows a copy icon in the top-right corner of the SQL diff container
2. Uses the `copyToClipboard` utility to copy the raw SQL text
3. Provides visual feedback by temporarily changing to a checkmark icon after copying
4. Reverts back to the copy icon after a delay using a custom hook (`useDelayedCaller`)

This implementation helps users easily capture the SQL differences for sharing or applying to their databases.

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




