/////////////////////////////////////////////////////////////
//
// pgAdmin 4 - PostgreSQL Tools
//
// Copyright (C) 2013 - 2025, The pgAdmin Development Team
// This software is released under the PostgreSQL Licence
//
//////////////////////////////////////////////////////////////

// Helper function to parse and color code SQL differences
export const parseAndColorCodeDiff = (diffSQL) => {
  if (!diffSQL) return null;

  // Split the SQL into lines
  const lines = diffSQL.split('\n');
  let coloredDiff = '';
  
  // Common SQL keywords that indicate operations
  const addedKeywords = ['CREATE', 'INSERT', 'ADD'];
  const removedKeywords = ['DROP', 'DELETE', 'REMOVE'];
  const modifiedKeywords = ['ALTER', 'UPDATE', 'MODIFY', 'REPLACE'];
  
  // Regular expressions for more precise matching
  const addedRegex = /^\+|^\s*CREATE\s|^\s*INSERT\s|ADD\s|ADDED:/i;
  const removedRegex = /^\-|^\s*DROP\s|^\s*DELETE\s|REMOVE\s|REMOVED:|MISSING:/i;
  const modifiedRegex = /^\s*ALTER\s|^\s*UPDATE\s|MODIFY\s|MODIFIED:|CHANGED:/i;

  for (const line of lines) {
    if (addedRegex.test(line)) {
      coloredDiff += `<span class="diff-added">${line}</span>\n`;
    } else if (removedRegex.test(line)) {
      coloredDiff += `<span class="diff-removed">${line}</span>\n`;
    } else if (modifiedRegex.test(line)) {
      coloredDiff += `<span class="diff-modified">${line}</span>\n`;
    } else {
      // Check if line contains any of the keywords
      const hasAddedKeyword = addedKeywords.some(keyword => line.includes(keyword));
      const hasRemovedKeyword = removedKeywords.some(keyword => line.includes(keyword));
      const hasModifiedKeyword = modifiedKeywords.some(keyword => line.includes(keyword));
      
      if (hasAddedKeyword && !hasRemovedKeyword && !hasModifiedKeyword) {
        coloredDiff += `<span class="diff-added">${line}</span>\n`;
      } else if (hasRemovedKeyword && !hasAddedKeyword && !hasModifiedKeyword) {
        coloredDiff += `<span class="diff-removed">${line}</span>\n`;
      } else if (hasModifiedKeyword) {
        coloredDiff += `<span class="diff-modified">${line}</span>\n`;
      } else {
        coloredDiff += line + '\n';
      }
    }
  }

  return coloredDiff;
}; 