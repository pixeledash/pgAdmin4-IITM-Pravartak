/////////////////////////////////////////////////////////////
//
// pgAdmin 4 - PostgreSQL Tools
//
// Copyright (C) 2013 - 2025, The pgAdmin Development Team
// This software is released under the PostgreSQL Licence
//
//////////////////////////////////////////////////////////////

import React from 'react';
import {
  Box, FormControl, InputLabel, Select, MenuItem, Button,
  Slider, Typography, Checkbox, FormControlLabel, Divider
} from '@mui/material';
import PropTypes from 'prop-types';
import gettext from 'sources/gettext';

export default function ExportDialog({ onClose, onExport }) {
  const [format, setFormat] = React.useState('png');
  const [quality, setQuality] = React.useState(90);
  const [highResolution, setHighResolution] = React.useState(false);

  const handleExport = () => {
    onExport(format, {
      quality: quality,
      highResolution: highResolution,
    });
    onClose();
  };

  // Only show quality slider for formats that support it
  const showQualityOption = ['jpeg', 'jpg', 'webp'].includes(format);
  
  return (
    <Box sx={{ p: 2, minWidth: 400 }}>
      <FormControl fullWidth sx={{ mb: 2 }}>
        <InputLabel>{gettext('Export Format')}</InputLabel>
        <Select
          value={format}
          label={gettext('Export Format')}
          onChange={(e) => setFormat(e.target.value)}
        >
          <MenuItem value="png">PNG</MenuItem>
          {/* <MenuItem value="svg">SVG</MenuItem> */}
          <MenuItem value="jpeg">JPEG</MenuItem>
          <MenuItem value="webp">WebP</MenuItem>
          <MenuItem value="pdf">PDF</MenuItem>
        </Select>
      </FormControl>

      {showQualityOption && (
        <Box sx={{ mb: 2 }}>
          <Typography id="quality-slider" gutterBottom>
            {gettext('Quality')}
          </Typography>
          <Slider
            value={quality}
            onChange={(e, newValue) => setQuality(newValue)}
            aria-labelledby="quality-slider"
            valueLabelDisplay="auto"
            min={10}
            max={100}
          />
        </Box>
      )}

      <Box sx={{ mb: 2 }}>
        <FormControlLabel
          control={
            <Checkbox 
              checked={highResolution} 
              onChange={(e) => setHighResolution(e.target.checked)} 
            />
          }
          label={gettext('High resolution (2x)')}
        />
      </Box>

      <Divider sx={{ my: 2 }} />
      
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
        <Button onClick={onClose}>{gettext('Cancel')}</Button>
        <Button variant="contained" onClick={handleExport}>
          {gettext('Export')}
        </Button>
      </Box>
    </Box>
  );
}

ExportDialog.propTypes = {
  onClose: PropTypes.func.isRequired,
  onExport: PropTypes.func.isRequired,
}; 