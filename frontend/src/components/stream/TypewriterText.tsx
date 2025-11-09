/**
 * Typewriter effect component - ChatGPT-style text animation
 */

'use client';

import { useState, useEffect } from 'react';

interface TypewriterTextProps {
  text: string;
  speed?: number; // milliseconds per character
  onComplete?: () => void;
  className?: string;
}

export function TypewriterText({ 
  text, 
  speed = 20, 
  onComplete,
  className = '' 
}: TypewriterTextProps) {
  const [displayedText, setDisplayedText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayedText(text.substring(0, currentIndex + 1));
        setCurrentIndex(currentIndex + 1);
      }, speed);

      return () => clearTimeout(timer);
    } else if (!isComplete) {
      setIsComplete(true);
      onComplete?.();
    }
  }, [currentIndex, text, speed, onComplete, isComplete]);

  // Reset when text changes
  useEffect(() => {
    setDisplayedText('');
    setCurrentIndex(0);
    setIsComplete(false);
  }, [text]);

  return (
    <span className={className}>
      {displayedText}
      {!isComplete && (
        <span className="inline-block w-1 h-4 bg-green-500 ml-0.5 animate-pulse" />
      )}
    </span>
  );
}

interface StreamingMessageProps {
  content: string;
  type: 'thought' | 'tool' | 'output' | 'analysis' | 'system';
  animate?: boolean;
  speed?: number;
}

export function StreamingMessage({ 
  content, 
  type, 
  animate = true,
  speed = 15 
}: StreamingMessageProps) {
  const [shouldAnimate, setShouldAnimate] = useState(animate);

  // Skip animation for very long content
  useEffect(() => {
    if (content.length > 500) {
      setShouldAnimate(false);
    }
  }, [content]);

  const getTypeStyles = () => {
    switch (type) {
      case 'thought':
        return 'text-purple-300 italic';
      case 'tool':
        return 'text-blue-300 font-medium';
      case 'output':
        return 'text-gray-300 font-mono text-sm';
      case 'analysis':
        return 'text-indigo-300';
      case 'system':
        return 'text-green-300';
      default:
        return 'text-gray-300';
    }
  };

  return (
    <div className={getTypeStyles()}>
      {shouldAnimate ? (
        <TypewriterText text={content} speed={speed} />
      ) : (
        <span>{content}</span>
      )}
    </div>
  );
}

