# LaTeX/PDF Conversion Workflow

## Current Process for Mathematical Documentation

### 1. **Pandoc Configuration**
- Use `enumitem` package with custom settings:
```latex
\usepackage{enumitem}
\setlist[itemize]{leftmargin=*, label=\\textbullet}
\setlist[enumerate,1]{label=\arabic*.}
```
- Document class: report (for table of contents)
- Geometry: margin=1in

### 2. **Handling Special Characters**
- Mathematical symbols render correctly except for some emoji-like characters
- Common warnings about missing characters but PDF renders acceptably

### 3. **LaTeX Equation Preservation**
All `$$...$$` display math blocks convert properly to LaTeX equations

## Future Improvements Needed

1. Fix font issues for ⚠️, ✓ and other special symbols
2. Add custom theorem environments for research documents
3. Implement bibliography integration via Zotero