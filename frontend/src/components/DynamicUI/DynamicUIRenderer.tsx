/**
 * DynamicUI Renderer
 * Renders adaptive UI components based on cognitive load and content
 */

import React, { useMemo, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Volume2, VolumeX, Pause, Play } from 'lucide-react';
import { voiceNarration } from '@/services/voiceNarration';
import type {
  UIComponent,
  UIComponentTree,
  PresentationConfig,
  TeachingModule,
  CognitiveLoad,
} from '@/types';

interface DynamicUIRendererProps {
  componentTree: UIComponentTree;
  currentModule?: TeachingModule;
  cognitiveLoad?: CognitiveLoad;
  onModuleComplete?: () => void;
  onNeedHelp?: () => void;
}

export const DynamicUIRenderer: React.FC<DynamicUIRendererProps> = ({
  componentTree,
  currentModule,
  cognitiveLoad = 'medium',
  onModuleComplete,
  onNeedHelp,
}) => {
  const config = componentTree.presentation_config;
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  // Check if this is the last module
  const isLastModule = componentTree.metadata?.current_module === componentTree.metadata?.total_modules;

  // Initialize voice narration
  useEffect(() => {
    // Check if speech synthesis is supported
    if ('speechSynthesis' in window) {
      console.log('Speech synthesis supported');
    } else {
      console.warn('Speech synthesis not supported in this browser');
    }
  }, []);

  // Speak module content when it changes
  useEffect(() => {
    if (voiceEnabled && currentModule) {
      setIsSpeaking(true);
      voiceNarration
        .speakModule(currentModule.title, currentModule.content, cognitiveLoad)
        .then(() => {
          setIsSpeaking(false);
        })
        .catch((error) => {
          console.error('Voice narration error:', error);
          setIsSpeaking(false);
        });
    }

    // Cleanup: stop speaking when component unmounts or module changes
    return () => {
      voiceNarration.stop();
      setIsSpeaking(false);
    };
  }, [currentModule, voiceEnabled, cognitiveLoad]);

  // Toggle voice narration
  const handleToggleVoice = () => {
    const newState = voiceNarration.toggle();
    setVoiceEnabled(newState);
    
    if (!newState) {
      setIsSpeaking(false);
      setIsPaused(false);
    }
  };

  // Pause/Resume narration
  const handlePauseResume = () => {
    if (isPaused) {
      voiceNarration.resume();
      setIsPaused(false);
    } else {
      voiceNarration.pause();
      setIsPaused(true);
    }
  };

  // Stop narration
  const handleStop = () => {
    voiceNarration.stop();
    setIsSpeaking(false);
    setIsPaused(false);
  };

  // Animation variants based on cognitive load
  const animationVariants = useMemo(() => {
    const speed = config.animation_speed;
    const duration = speed === 'slow' ? 0.8 : speed === 'fast' ? 0.3 : 0.5;

    return {
      initial: { opacity: 0, y: 20, scale: 0.95 },
      animate: {
        opacity: 1,
        y: 0,
        scale: 1,
        transition: {
          duration,
          ease: 'easeOut'
        }
      },
      exit: {
        opacity: 0,
        y: -20,
        scale: 0.95,
        transition: {
          duration: duration * 0.7,
          ease: 'easeIn'
        }
      },
    };
  }, [config.animation_speed]);

  // Card hover animation
  const cardHoverVariants = {
    hover: {
      scale: 1.02,
      boxShadow: '0 10px 30px rgba(0, 0, 0, 0.15)',
      transition: { duration: 0.2 }
    }
  };

  // Button animation
  const buttonVariants = {
    hover: { scale: 1.05, transition: { duration: 0.2 } },
    tap: { scale: 0.95, transition: { duration: 0.1 } }
  };

  // Font size mapping
  const fontSizeClass = useMemo(() => {
    switch (config.font_size) {
      case 'small':
        return 'text-sm';
      case 'large':
        return 'text-lg';
      default:
        return 'text-base';
    }
  }, [config.font_size]);

  // Render individual component
  const renderComponent = (component: UIComponent): React.ReactNode => {
    const { type, props, children } = component;

    switch (type) {
      case 'Container':
        return (
          <div key={component.id} className={`p-4 ${props.className || ''}`}>
            {children?.map(renderComponent)}
          </div>
        );

      case 'Card':
        return (
          <motion.div
            key={component.id}
            className={`bg-white rounded-lg shadow-lg p-6 mb-4 ${props.className || ''}`}
            {...animationVariants}
            whileHover="hover"
            variants={cardHoverVariants}
          >
            {children?.map(renderComponent)}
          </motion.div>
        );

      case 'Heading':
        const HeadingTag = (props.level || 'h2') as keyof JSX.IntrinsicElements;
        return (
          <HeadingTag
            key={component.id}
            className={`font-bold mb-4 ${fontSizeClass} ${props.className || ''}`}
          >
            {props.text}
          </HeadingTag>
        );

      case 'Text':
        return (
          <p
            key={component.id}
            className={`mb-3 ${fontSizeClass} ${props.className || ''}`}
          >
            {props.text}
          </p>
        );

      case 'CodeBlock':
        return (
          <div key={component.id} className="mb-4">
            <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
              <code className={`language-${props.language || 'javascript'}`}>
                {props.code}
              </code>
            </pre>
          </div>
        );

      case 'List':
        return (
          <ul key={component.id} className={`list-disc list-inside mb-4 ${fontSizeClass}`}>
            {props.items?.map((item: string, index: number) => (
              <li key={index} className="mb-2">
                {item}
              </li>
            ))}
          </ul>
        );

      case 'Button':
        return (
          <button
            key={component.id}
            onClick={props.onClick}
            className={`px-6 py-3 rounded-lg font-semibold transition-colors ${
              props.variant === 'primary'
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
            } ${props.className || ''}`}
          >
            {props.text}
          </button>
        );

      case 'ProgressBar':
        return (
          <div key={component.id} className="mb-4">
            <div className="flex justify-between text-sm mb-2">
              <span>{props.label}</span>
              <span>{props.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <motion.div
                className="bg-blue-600 h-2 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${props.progress}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>
        );

      case 'Alert':
        const alertColors = {
          info: 'bg-blue-100 border-blue-500 text-blue-900',
          warning: 'bg-yellow-100 border-yellow-500 text-yellow-900',
          error: 'bg-red-100 border-red-500 text-red-900',
          success: 'bg-green-100 border-green-500 text-green-900',
        };
        return (
          <div
            key={component.id}
            className={`border-l-4 p-4 mb-4 ${alertColors[props.type || 'info']}`}
          >
            {props.text}
          </div>
        );

      case 'Divider':
        return <hr key={component.id} className="my-6 border-gray-300" />;

      case 'Spacer':
        return <div key={component.id} className={`h-${props.size || 4}`} />;

      case 'Header':
        return (
          <div key={component.id} className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{props.title}</h1>
            {props.complexity && (
              <span className="text-sm text-gray-600 capitalize">
                Complexity: {props.complexity}
              </span>
            )}
            {props.estimatedTime && (
              <span className="text-sm text-gray-600 ml-4">
                Est. Time: {props.estimatedTime} min
              </span>
            )}
          </div>
        );

      case 'ModulesContainer':
        return (
          <div key={component.id} className="space-y-4">
            {children?.map(renderComponent)}
          </div>
        );

      case 'ExplanationModule':
      case 'CodeExampleModule':
      case 'InteractiveDemoModule':
      case 'VisualDiagramModule':
      case 'StepByStepModule':
      case 'QuickReferenceModule':
      case 'GenericModule':
        return (
          <motion.div
            key={component.id}
            className="bg-white rounded-lg shadow-md p-6 mb-4 hover:shadow-xl transition-shadow"
            {...animationVariants}
            whileHover="hover"
            variants={cardHoverVariants}
          >
            <h3 className="text-xl font-semibold mb-3">{props.title}</h3>
            <div className="prose max-w-none">
              <p className={fontSizeClass} style={{ whiteSpace: 'pre-wrap' }}>{props.content}</p>
            </div>
            {props.estimatedTime && (
              <div className="mt-4 text-sm text-gray-500">
                Estimated time: {props.estimatedTime} seconds
              </div>
            )}
            {children?.map(renderComponent)}
          </motion.div>
        );

      case 'Navigation':
        return (
          <div key={component.id} className="mt-6 flex justify-between items-center">
            <span className="text-sm text-gray-600">
              Module {props.currentModule || 1} of {props.totalModules || 1}
            </span>
          </div>
        );

      case 'SourceReferences':
        return (
          <details key={component.id} className="mt-6">
            <summary className="cursor-pointer text-sm font-semibold text-gray-700">
              Sources & References
            </summary>
            <div className="mt-2 space-y-2">
              {props.sources?.map((source: any, index: number) => (
                <div key={index} className="text-sm text-gray-600">
                  <a href={source.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                    {source.title}
                  </a>
                  {source.relevance && (
                    <span className="ml-2 text-gray-500">
                      (Relevance: {(source.relevance * 100).toFixed(0)}%)
                    </span>
                  )}
                </div>
              ))}
            </div>
          </details>
        );

      case 'CodeSnippet':
        return (
          <div key={component.id} className="mb-4">
            <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
              <code className={`language-${props.language || 'javascript'}`}>
                {props.content}
              </code>
            </pre>
          </div>
        );

      default:
        console.warn(`Unknown component type: ${type}`);
        return null;
    }
  };

  // Render cognitive load indicator
  const renderCognitiveLoadIndicator = () => {
    const colors = {
      low: 'bg-green-500',
      medium: 'bg-yellow-500',
      high: 'bg-red-500',
    };

    const labels = {
      low: 'Relaxed',
      medium: 'Focused',
      high: 'Intense',
    };

    return (
      <div className="flex items-center gap-2 text-sm">
        <div className={`w-3 h-3 rounded-full ${colors[cognitiveLoad]}`} />
        <span className="text-gray-600">{labels[cognitiveLoad]}</span>
      </div>
    );
  };

  // Render module controls
  const renderModuleControls = () => {
    if (!currentModule) return null;

    return (
      <div className="flex gap-3 mt-6">
        <motion.button
          onClick={onModuleComplete}
          className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors shadow-md"
          variants={buttonVariants}
          whileHover="hover"
          whileTap="tap"
        >
          {isLastModule ? '✓ Complete Session' : 'Continue →'}
        </motion.button>
        <motion.button
          onClick={onNeedHelp}
          className="px-6 py-3 bg-gray-200 text-gray-800 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
          variants={buttonVariants}
          whileHover="hover"
          whileTap="tap"
        >
          Need Help
        </motion.button>
      </div>
    );
  };

  return (
    <div className={`dynamic-ui-container ${fontSizeClass}`}>
      {/* Header with cognitive load indicator and voice controls */}
      <div className="flex justify-between items-center mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex-1">
          {currentModule && (
            <div>
              <h3 className="font-semibold text-lg">{currentModule.title}</h3>
              <p className="text-sm text-gray-600">
                {currentModule.type.replace('_', ' ')} • {currentModule.estimated_time} min
              </p>
            </div>
          )}
        </div>
        <div className="flex items-center gap-4">
          {renderCognitiveLoadIndicator()}
          
          {/* Voice Controls */}
          <div className="flex items-center gap-2 border-l pl-4">
            <button
              onClick={handleToggleVoice}
              className={`p-2 rounded-lg transition-colors ${
                voiceEnabled
                  ? 'bg-blue-100 text-blue-600 hover:bg-blue-200'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
              title={voiceEnabled ? 'Disable voice narration' : 'Enable voice narration'}
            >
              {voiceEnabled ? <Volume2 className="w-5 h-5" /> : <VolumeX className="w-5 h-5" />}
            </button>
            
            {voiceEnabled && isSpeaking && (
              <button
                onClick={handlePauseResume}
                className="p-2 rounded-lg bg-blue-100 text-blue-600 hover:bg-blue-200 transition-colors"
                title={isPaused ? 'Resume narration' : 'Pause narration'}
              >
                {isPaused ? <Play className="w-5 h-5" /> : <Pause className="w-5 h-5" />}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Voice status indicator */}
      {voiceEnabled && (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isSpeaking ? 'bg-blue-600 animate-pulse' : 'bg-gray-400'}`} />
            <span className="text-sm text-blue-900">
              {isSpeaking ? (isPaused ? 'Voice paused' : 'Voice narration active') : 'Voice ready'}
            </span>
          </div>
          {isSpeaking && (
            <button
              onClick={handleStop}
              className="text-xs text-blue-600 hover:text-blue-800 font-medium"
            >
              Stop
            </button>
          )}
        </div>
      )}

      {/* Main content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={componentTree.root.id}
          {...animationVariants}
          className="content-area"
        >
          {renderComponent(componentTree.root)}
        </motion.div>
      </AnimatePresence>

      {/* Module controls */}
      {renderModuleControls()}
    </div>
  );
};

export default DynamicUIRenderer;

// Made with Bob for IBM AI Builders Challenge