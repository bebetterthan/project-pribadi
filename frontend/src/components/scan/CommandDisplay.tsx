import React from 'react';
import { Card, CardContent, Typography, Box, Chip } from '@mui/material';
import { Terminal, Timer, Info } from '@mui/icons-material';

interface CommandDisplayProps {
  tool: string;
  command: string;
  explanation?: string;
  estimatedTime?: string;
}

export const CommandDisplay: React.FC<CommandDisplayProps> = ({
  tool,
  command,
  explanation,
  estimatedTime
}) => {
  return (
    <Card 
      sx={{ 
        mb: 2, 
        bgcolor: '#1e1e1e', 
        border: '1px solid #333',
        fontFamily: 'monospace'
      }}
    >
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          <Terminal sx={{ mr: 1, color: '#4CAF50' }} />
          <Typography variant="h6" sx={{ color: '#4CAF50' }}>
            {tool.toUpperCase()} - Command Execution
          </Typography>
        </Box>

        {explanation && (
          <Box display="flex" alignItems="flex-start" mb={2}>
            <Info sx={{ mr: 1, color: '#2196F3', fontSize: 20 }} />
            <Typography variant="body2" sx={{ color: '#bbb' }}>
              {explanation}
            </Typography>
          </Box>
        )}

        <Box 
          sx={{ 
            bgcolor: '#000', 
            p: 2, 
            borderRadius: 1,
            border: '1px solid #444',
            overflowX: 'auto'
          }}
        >
          <Typography 
            component="pre" 
            sx={{ 
              color: '#00ff00', 
              fontSize: '0.875rem',
              margin: 0,
              fontFamily: '"Courier New", monospace'
            }}
          >
            $ {command}
          </Typography>
        </Box>

        {estimatedTime && (
          <Box display="flex" alignItems="center" mt={2}>
            <Timer sx={{ mr: 1, color: '#FFC107', fontSize: 18 }} />
            <Typography variant="caption" sx={{ color: '#999' }}>
              Estimated Time: {estimatedTime}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

