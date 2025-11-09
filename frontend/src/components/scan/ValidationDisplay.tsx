import React from 'react';
import { Card, CardContent, Typography, Box, LinearProgress, Chip } from '@mui/material';
import { CheckCircle, Cancel, Dns } from '@mui/icons-material';

interface ValidationResults {
  total_tested: number;
  valid_count: number;
  invalid_count: number;
  validation_rate: string;
  valid_subdomains?: Array<{subdomain: string; ip: string}>;
  invalid_subdomains?: Array<{subdomain: string; reason: string}>;
}

interface ValidationDisplayProps {
  results: ValidationResults;
  isComplete: boolean;
}

export const ValidationDisplay: React.FC<ValidationDisplayProps> = ({
  results,
  isComplete
}) => {
  const validPercentage = (results.valid_count / results.total_tested) * 100;

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
          <Dns sx={{ mr: 1, color: '#2196F3' }} />
          <Typography variant="h6" sx={{ color: '#2196F3' }}>
            🔍 DNS Validation {isComplete ? '- Complete' : '- In Progress'}
          </Typography>
        </Box>

        <Box mb={3}>
          <Box display="flex" justifyContent="space-between" mb={1}>
            <Typography variant="body2" sx={{ color: '#bbb' }}>
              Validation Progress
            </Typography>
            <Typography variant="body2" sx={{ color: '#4caf50', fontWeight: 'bold' }}>
              {results.validation_rate}
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={validPercentage} 
            sx={{
              height: 10,
              borderRadius: 5,
              bgcolor: '#333',
              '& .MuiLinearProgress-bar': {
                bgcolor: '#4caf50'
              }
            }}
          />
        </Box>

        <Box display="flex" gap={2} mb={3}>
          <Box flex={1}>
            <Chip 
              icon={<CheckCircle />}
              label={`${results.valid_count} Valid`}
              color="success"
              sx={{ width: '100%' }}
            />
          </Box>
          <Box flex={1}>
            <Chip 
              icon={<Cancel />}
              label={`${results.invalid_count} Invalid`}
              color="error"
              sx={{ width: '100%' }}
            />
          </Box>
        </Box>

        {isComplete && results.valid_subdomains && results.valid_subdomains.length > 0 && (
          <Box>
            <Typography variant="subtitle2" sx={{ color: '#4caf50', mb: 1 }}>
              ✅ Valid Subdomains (showing first 5):
            </Typography>
            <Box 
              sx={{ 
                bgcolor: '#000', 
                p: 2, 
                borderRadius: 1,
                maxHeight: '150px',
                overflowY: 'auto'
              }}
            >
              {results.valid_subdomains.slice(0, 5).map((item, index) => (
                <Typography 
                  key={index}
                  variant="body2" 
                  sx={{ 
                    color: '#4caf50', 
                    fontFamily: 'monospace',
                    fontSize: '0.875rem'
                  }}
                >
                  • {item.subdomain} → {item.ip}
                </Typography>
              ))}
              {results.valid_subdomains.length > 5 && (
                <Typography 
                  variant="caption" 
                  sx={{ color: '#888', fontStyle: 'italic' }}
                >
                  ... and {results.valid_subdomains.length - 5} more
                </Typography>
              )}
            </Box>
          </Box>
        )}

        {isComplete && (
          <Box mt={2}>
            <Typography variant="caption" sx={{ color: '#888' }}>
              💡 Only valid subdomains will be scanned by subsequent tools
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

