/**
 * Expandable effects panel for call controls.
 *
 * Shows above the call controls with:
 * - Audio effects (noise cancellation, voice presets)
 * - Video effects (background blur, beauty filter)
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Mic2, Camera, Sparkles, Waves } from 'lucide-react';

export interface EffectsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  isVideoEnabled?: boolean;
}

interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
}

function Switch({ checked, onChange }: SwitchProps) {
  return (
    <button
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative w-10 h-6 rounded-full transition-colors ${
        checked ? 'bg-accent-red' : 'bg-discord-bg-modifier-active'
      }`}
    >
      <motion.div
        className="absolute top-1 left-1 w-4 h-4 bg-white rounded-full"
        animate={{ x: checked ? 16 : 0 }}
        transition={{ type: 'spring', stiffness: 500, damping: 30 }}
      />
    </button>
  );
}

interface EffectToggleProps {
  icon: React.ReactNode;
  name: string;
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
}

function EffectToggle({ icon, name, enabled, onToggle }: EffectToggleProps) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <span className="text-discord-text-muted">{icon}</span>
        <span className="text-sm text-discord-text-primary">{name}</span>
      </div>
      <Switch checked={enabled} onChange={onToggle} />
    </div>
  );
}

export function EffectsPanel({ isOpen, onClose, isVideoEnabled = false }: EffectsPanelProps) {
  // Audio effects state
  const [noiseCancellation, setNoiseCancellation] = useState(false);
  const [echoReduction, setEchoReduction] = useState(false);

  // Video effects state
  const [backgroundBlur, setBackgroundBlur] = useState(false);
  const [beautyFilter, setBeautyFilter] = useState(false);

  // Handlers with console.log for now (Phase 9 effects API integration later)
  const handleNoiseCancellation = (enabled: boolean) => {
    console.log('Noise cancellation:', enabled);
    setNoiseCancellation(enabled);
  };

  const handleEchoReduction = (enabled: boolean) => {
    console.log('Echo reduction:', enabled);
    setEchoReduction(enabled);
  };

  const handleBackgroundBlur = (enabled: boolean) => {
    console.log('Background blur:', enabled);
    setBackgroundBlur(enabled);
  };

  const handleBeautyFilter = (enabled: boolean) => {
    console.log('Beauty filter:', enabled);
    setBeautyFilter(enabled);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          transition={{ type: 'spring', stiffness: 400, damping: 30 }}
          className="absolute bottom-20 left-1/2 -translate-x-1/2 w-80 bg-discord-bg-secondary rounded-lg shadow-xl border border-discord-bg-tertiary overflow-hidden z-50"
        >
          {/* Header */}
          <div className="px-4 py-3 border-b border-discord-bg-tertiary flex items-center justify-between">
            <h4 className="font-medium text-discord-text-primary flex items-center gap-2">
              <Sparkles size={16} />
              Effects
            </h4>
            <button
              onClick={onClose}
              className="text-discord-text-muted hover:text-discord-text-primary transition-colors p-1 rounded hover:bg-discord-bg-modifier-hover"
            >
              <X size={18} />
            </button>
          </div>

          {/* Content */}
          <div className="p-4 space-y-6">
            {/* Audio Effects */}
            <div className="space-y-3">
              <h5 className="text-xs font-semibold uppercase tracking-wider text-discord-text-muted flex items-center gap-2">
                <Mic2 size={14} />
                Audio Effects
              </h5>
              <div className="space-y-3">
                <EffectToggle
                  icon={<Waves size={18} />}
                  name="Noise Cancellation"
                  enabled={noiseCancellation}
                  onToggle={handleNoiseCancellation}
                />
                <EffectToggle
                  icon={<Mic2 size={18} />}
                  name="Echo Reduction"
                  enabled={echoReduction}
                  onToggle={handleEchoReduction}
                />
              </div>
            </div>

            {/* Video Effects - only shown when video is enabled */}
            {isVideoEnabled && (
              <div className="space-y-3">
                <h5 className="text-xs font-semibold uppercase tracking-wider text-discord-text-muted flex items-center gap-2">
                  <Camera size={14} />
                  Video Effects
                </h5>
                <div className="space-y-3">
                  <EffectToggle
                    icon={<Camera size={18} />}
                    name="Background Blur"
                    enabled={backgroundBlur}
                    onToggle={handleBackgroundBlur}
                  />
                  <EffectToggle
                    icon={<Sparkles size={18} />}
                    name="Beauty Filter"
                    enabled={beautyFilter}
                    onToggle={handleBeautyFilter}
                  />
                </div>
              </div>
            )}

            {/* Hint text */}
            <p className="text-xs text-discord-text-muted pt-2 border-t border-discord-bg-tertiary">
              Effects are processed locally on your device.
            </p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
