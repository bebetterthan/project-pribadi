import React, { useEffect, useRef } from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { Code } from '@mui/icons-material';

interface OutputLine {
  content: string;
  timestamp: string;
  lineNumber?: number;
}

interface LiveOutputConsoleProps {
  tool: string;
  lines: OutputLine[];
  autoScroll?: boolean;
}

export const LiveOutputConsole: React.FC<LiveOutputConsoleProps> = ({
  tool,
  lines,
  autoScroll = true
}) => {
  const consoleEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [lines, autoScroll]);

  const getLineColor = (content: string): string => {
    // Color coding based on content
    if (content.includes('ERROR') || content.includes('❌')) return '#f44336';
    if (content.includes('WARNING') || content.includes('⚠️')) return '#ff9800';
    if (content.includes('SUCCESS') || content.includes('✅') || content.includes('Found:')) return '#4caf50';
    if (content.includes('INFO') || content.includes('ℹ️')) return '#2196f3';
    return '#e0e0e0';
  };

  return (
    <Card 
      sx={{ 
        mb: 2, 
        bgcolor: '#1e1e1e',
        border: '1px solid #333'
      }}
    >
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          <Code sx={{ mr: 1, color: '#00ff00' }} />
          <Typography variant="h6" sx={{ color: '#00ff00' }}>
            📊 Live Output - {tool.toUpperCase()}
          </Typography>
          <Box ml="auto">
            <Typography variant="caption" sx={{ color: '#888' }}>
              {lines.length} lines
            </Typography>
          </Box>
        </Box>

        <Box 
          sx={{ 
            bgcolor: '#000', 
            p: 2, 
            borderRadius: 1,
            border: '1px solid #444',
            maxHeight: '400px',
            overflowY: 'auto',
            fontFamily: '"Courier New", monospace'
          }}
        >
          {lines.length === 0 ? (
            <Typography sx={{ color: '#666', fontStyle: 'italic' }}>
              Waiting for output...
            </Typography>
          ) : (
            lines.map((line, index) => (
              <Box key={index} display="flex" sx={{ mb: 0.5 }}>
                <Typography 
                  component="span" 
                  sx={{ 
                    color: '#666', 
                    mr: 2, 
                    minWidth: '40px',
                    fontSize: '0.75rem'
                  }}
                >
                  {line.lineNumber || index + 1}
                </Typography>
                <Typography 
                  component="pre" 
                  sx={{ 
                    color: getLineColor(line.content),
                    fontSize: '0.875rem',
                    margin: 0,
                    flex: 1,
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word'
                  }}
                >
                  {line.content}
                </Typography>
              </Box>
            ))
          )}
          <div ref={consoleEndRef} />
        </Box>
      </CardContent>
    </Card>
  );
};

