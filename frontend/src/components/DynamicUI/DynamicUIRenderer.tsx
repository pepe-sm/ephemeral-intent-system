/**
 * DynamicUI Renderer
 * Renders adaptive UI components based on cognitive load and content
 */

import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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

  // Animation variants based on cognitive load
  const animationVariants = useMemo(() => {
    const speed = config.animation_speed;
    const duration = speed === 'slow' ? 0.8 : speed === 'fast' ? 0.3 : 0.5;

    return {
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0, transition: { duration } },
      exit: { opacity: 0, y: -20, transition: { duration: duration * 0.7 } },
    };
  }, [config.animation_speed]);

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
        <button
          onClick={onModuleComplete}
          className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
        >
          Continue
        </button>
        <button
          onClick={onNeedHelp}
          className="px-6 py-3 bg-gray-200 text-gray-800 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
        >
          Need Help
        </button>
      </div>
    );
  };

  return (
    <div className={`dynamic-ui-container ${fontSizeClass}`}>
      {/* Header with cognitive load indicator */}
      <div className="flex justify-between items-center mb-6 p-4 bg-gray-50 rounded-lg">
        <div>
          {currentModule && (
            <div>
              <h3 className="font-semibold text-lg">{currentModule.title}</h3>
              <p className="text-sm text-gray-600">
                {currentModule.type.replace('_', ' ')} • {currentModule.estimated_time} min
              </p>
            </div>
          )}
        </div>
        {renderCognitiveLoadIndicator()}
      </div>

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

      {/* Voice indicator (if enabled) */}
      {config.voice_enabled && (
        <div className="mt-4 p-3 bg-blue-50 rounded-lg flex items-center gap-2">
          <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
          <span className="text-sm text-blue-900">Voice guidance active</span>
        </div>
      )}
    </div>
  );
};

export default DynamicUIRenderer;

// Made with Bob for IBM AI Builders Challenge