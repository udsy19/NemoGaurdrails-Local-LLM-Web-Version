import React, { useState, useMemo, useCallback } from 'react';
import {
  Box,
  IconButton,
  Tooltip,
  Typography,
  Tabs,
  Tab,
  Paper,
  Chip,
} from '@mui/material';
import {
  ContentCopy as CopyIcon,
  Check as CheckIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

interface CodeExample {
  language: string;
  code: string;
  filename?: string;
}

interface CodeBlockProps {
  examples: CodeExample[];
  title?: string;
  description?: string;
}

const CodeBlock: React.FC<CodeBlockProps> = React.memo(({ examples, title, description }) => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(examples[selectedTab].code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  }, [examples, selectedTab]);

  const getLanguageColor = (language: string) => {
    const colors: { [key: string]: string } = {
      python: '#3776ab',
      javascript: '#f7df1e',
      typescript: '#3178c6',
      java: '#ed8b00',
      'c++': '#00599c',
      c: '#a8b9cc',
      go: '#00add8',
      rust: '#000000',
      php: '#777bb4',
      ruby: '#cc342d',
      shell: '#89e051',
      bash: '#89e051',
      json: '#000000',
      yaml: '#cb171e',
      xml: '#0060ac',
      sql: '#e38c00'
    };
    return colors[language.toLowerCase()] || '#6b7280';
  };

  const syntaxHighlight = (code: string, language: string) => {
    const keywords: { [key: string]: string[] } = {
      python: ['def', 'class', 'import', 'from', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally', 'with', 'as', 'return', 'yield', 'lambda', 'and', 'or', 'not', 'in', 'is', 'True', 'False', 'None', 'async', 'await'],
      javascript: ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue', 'return', 'try', 'catch', 'finally', 'throw', 'new', 'this', 'class', 'extends', 'super', 'async', 'await', 'true', 'false', 'null', 'undefined'],
      typescript: ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue', 'return', 'try', 'catch', 'finally', 'throw', 'new', 'this', 'class', 'extends', 'super', 'async', 'await', 'true', 'false', 'null', 'undefined', 'interface', 'type', 'enum', 'public', 'private', 'protected'],
      java: ['public', 'private', 'protected', 'static', 'final', 'abstract', 'class', 'interface', 'extends', 'implements', 'import', 'package', 'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue', 'return', 'try', 'catch', 'finally', 'throw', 'throws', 'new', 'this', 'super', 'true', 'false', 'null', 'void', 'int', 'String', 'boolean', 'double', 'float', 'long', 'char'],
      'c++': ['#include', '#define', 'int', 'char', 'float', 'double', 'void', 'bool', 'true', 'false', 'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue', 'return', 'class', 'public', 'private', 'protected', 'virtual', 'static', 'const', 'namespace', 'using', 'std', 'cout', 'cin', 'endl'],
      c: ['#include', '#define', 'int', 'char', 'float', 'double', 'void', 'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue', 'return', 'struct', 'typedef', 'static', 'const', 'printf', 'scanf', 'malloc', 'free']
    };

    let highlightedCode = code;
    const langKeywords = keywords[language.toLowerCase()] || [];

    // Highlight strings
    highlightedCode = highlightedCode.replace(
      /(["'`])((?:\\.|(?!\1)[^\\])*?)\1/g,
      '<span style="color: #22c55e;">$1$2$1</span>'
    );

    // Highlight comments
    if (language.toLowerCase() === 'python') {
      highlightedCode = highlightedCode.replace(
        /(#.*$)/gm,
        '<span style="color: #6b7280; font-style: italic;">$1</span>'
      );
    } else if (['javascript', 'typescript', 'java', 'c++', 'c'].includes(language.toLowerCase())) {
      highlightedCode = highlightedCode.replace(
        /(\/\/.*$)/gm,
        '<span style="color: #6b7280; font-style: italic;">$1</span>'
      );
      highlightedCode = highlightedCode.replace(
        /(\/\*[\s\S]*?\*\/)/g,
        '<span style="color: #6b7280; font-style: italic;">$1</span>'
      );
    }

    // Highlight keywords
    langKeywords.forEach(keyword => {
      const regex = new RegExp(`\\b${keyword}\\b`, 'g');
      highlightedCode = highlightedCode.replace(
        regex,
        `<span style="color: #f59e0b; font-weight: 600;">${keyword}</span>`
      );
    });

    // Highlight numbers
    highlightedCode = highlightedCode.replace(
      /\b\d+\.?\d*\b/g,
      '<span style="color: #8b5cf6;">$&</span>'
    );

    // Highlight function calls
    highlightedCode = highlightedCode.replace(
      /(\w+)(\s*\()/g,
      '<span style="color: #06b6d4;">$1</span>$2'
    );

    return highlightedCode;
  };

  return (
    <Box sx={{ mb: 3 }}>
      {title && (
        <Typography variant="h6" sx={{ color: '#ffffff', mb: 1, fontWeight: 600 }}>
          {title}
        </Typography>
      )}
      {description && (
        <Typography variant="body2" sx={{ color: '#a1a1aa', mb: 2 }}>
          {description}
        </Typography>
      )}

      <Paper sx={{
        background: 'rgba(0, 0, 0, 0.4)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: 2,
        overflow: 'hidden'
      }}>
        {/* Header with tabs and copy button */}
        <Box sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          backgroundColor: 'rgba(255, 255, 255, 0.02)'
        }}>
          <Tabs
            value={selectedTab}
            onChange={(_, newValue) => setSelectedTab(newValue)}
            sx={{
              minHeight: 48,
              '& .MuiTab-root': {
                color: '#6b7280',
                textTransform: 'none',
                fontSize: '0.875rem',
                fontWeight: 500,
                minHeight: 48,
                '&.Mui-selected': {
                  color: '#00D4AA',
                },
              },
              '& .MuiTabs-indicator': {
                backgroundColor: '#00D4AA',
              },
            }}
          >
            {examples.map((example, index) => (
              <Tab
                key={index}
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip
                      size="small"
                      label={example.language}
                      sx={{
                        backgroundColor: getLanguageColor(example.language) + '20',
                        color: getLanguageColor(example.language),
                        fontSize: '0.7rem',
                        height: 20,
                      }}
                    />
                    {example.filename && (
                      <Typography variant="caption" sx={{ color: '#6b7280' }}>
                        {example.filename}
                      </Typography>
                    )}
                  </Box>
                }
              />
            ))}
          </Tabs>

          <Box sx={{ pr: 1 }}>
            <Tooltip title={copied ? 'Copied!' : 'Copy code'}>
              <IconButton
                onClick={handleCopy}
                size="small"
                sx={{
                  color: copied ? '#10b981' : '#6b7280',
                  '&:hover': {
                    color: copied ? '#10b981' : '#00D4AA',
                  }
                }}
              >
                <AnimatePresence mode="wait">
                  {copied ? (
                    <motion.div
                      key="check"
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      exit={{ scale: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <CheckIcon fontSize="small" />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="copy"
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      exit={{ scale: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <CopyIcon fontSize="small" />
                    </motion.div>
                  )}
                </AnimatePresence>
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Code content */}
        <Box sx={{
          p: 3,
          backgroundColor: '#0f172a',
          overflow: 'auto',
          maxHeight: '350px'
        }}>
          <Typography
            component="pre"
            sx={{
              fontFamily: '"JetBrains Mono", "Fira Code", "Monaco", "Consolas", monospace',
              fontSize: '0.875rem',
              lineHeight: 1.6,
              margin: 0,
              color: '#e2e8f0',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
            }}
            dangerouslySetInnerHTML={{
              __html: useMemo(() => 
                syntaxHighlight(examples[selectedTab].code, examples[selectedTab].language), 
                [examples, selectedTab]
              )
            }}
          />
        </Box>
      </Paper>
    </Box>
  );
});

export default CodeBlock;