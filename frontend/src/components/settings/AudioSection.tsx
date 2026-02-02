/**
 * Audio device settings section.
 *
 * Allows user to select:
 * - Microphone (input device)
 * - Speaker (output device)
 * - Test microphone functionality
 */

import { useState, useEffect } from 'react';
import { api } from '@/lib/pywebview';
import { Button } from '@/components/ui/Button';
import { Mic, Volume2, RefreshCw } from 'lucide-react';

interface AudioDevice {
  id: number;
  name: string;
  channels: number;
}

export function AudioSection() {
  const [inputDevices, setInputDevices] = useState<AudioDevice[]>([]);
  const [outputDevices, setOutputDevices] = useState<AudioDevice[]>([]);
  const [selectedInput, setSelectedInput] = useState<number | null>(null);
  const [selectedOutput, setSelectedOutput] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [testStatus, setTestStatus] = useState<string | null>(null);

  // Load devices on mount
  useEffect(() => {
    loadDevices();
  }, []);

  const loadDevices = async () => {
    setLoading(true);
    try {
      const result = await api.call((a) => a.get_audio_devices());
      if (!result.error) {
        setInputDevices(result.inputs || []);
        setOutputDevices(result.outputs || []);

        // Select first device if none selected
        if (result.inputs?.length && selectedInput === null) {
          const firstInput = result.inputs[0];
          if (firstInput) {
            setSelectedInput(firstInput.id);
          }
        }
        if (result.outputs?.length && selectedOutput === null) {
          const firstOutput = result.outputs[0];
          if (firstOutput) {
            setSelectedOutput(firstOutput.id);
          }
        }
      }
    } catch (error) {
      console.error('Failed to load audio devices:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = async (deviceId: number) => {
    setSelectedInput(deviceId);
    await api.call((a) => a.set_audio_devices(deviceId, selectedOutput));
  };

  const handleOutputChange = async (deviceId: number) => {
    setSelectedOutput(deviceId);
    await api.call((a) => a.set_audio_devices(selectedInput, deviceId));
  };

  const testMicrophone = async () => {
    if (testing || selectedInput === null) return;

    setTesting(true);
    setTestStatus('Recording...');
    try {
      // Start recording
      await api.call((a) => a.start_voice_recording());

      // Record for 2 seconds
      await new Promise((resolve) => setTimeout(resolve, 2000));

      setTestStatus('Processing...');
      const result = await api.call((a) => a.stop_voice_recording());

      if (result.error) {
        setTestStatus('Recording failed: ' + result.error);
        return;
      }

      if (result.id) {
        setTestStatus('Playing back...');
        // Get file data and play
        const fileResult = await api.call((a) => a.get_file(result.id as string));
        if (fileResult.data) {
          const audio = new Audio(`data:${fileResult.mimeType};base64,${fileResult.data}`);
          audio.onended = () => setTestStatus('Test complete!');
          audio.onerror = () => setTestStatus('Playback failed');
          await audio.play();
        } else {
          setTestStatus('Could not load recording');
        }
      } else {
        setTestStatus('Recording too short');
      }
    } catch (error) {
      console.error('Microphone test failed:', error);
      setTestStatus('Test failed');
    } finally {
      setTesting(false);
      // Clear status after 3 seconds
      setTimeout(() => setTestStatus(null), 3000);
    }
  };

  if (loading) {
    return (
      <section className="space-y-6">
        <h3 className="text-lg font-semibold text-discord-text-primary">
          Voice & Audio
        </h3>
        <div className="h-px bg-discord-bg-tertiary" />
        <p className="text-sm text-discord-text-muted">Loading devices...</p>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <h3 className="text-lg font-semibold text-discord-text-primary">
        Voice & Audio
      </h3>

      <div className="h-px bg-discord-bg-tertiary" />

      <div className="space-y-4">
        {/* Microphone selection */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <label className="text-sm font-medium text-discord-text-primary flex items-center gap-2">
              <Mic size={16} />
              Microphone
            </label>
            <p className="text-sm text-discord-text-muted mt-0.5">
              Select your input device for voice calls
            </p>
          </div>
          <select
            value={selectedInput ?? ''}
            onChange={(e) => handleInputChange(Number(e.target.value))}
            className="
              w-64 bg-discord-bg-tertiary border border-discord-bg-modifier-active
              rounded-md px-3 py-2 text-discord-text-primary
              focus:ring-2 focus:ring-accent-red focus:border-transparent
              focus:outline-none
            "
          >
            {inputDevices.length === 0 ? (
              <option value="">No microphones found</option>
            ) : (
              inputDevices.map((device) => (
                <option key={device.id} value={device.id}>
                  {device.name}
                </option>
              ))
            )}
          </select>
        </div>

        {/* Speaker selection */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <label className="text-sm font-medium text-discord-text-primary flex items-center gap-2">
              <Volume2 size={16} />
              Speaker
            </label>
            <p className="text-sm text-discord-text-muted mt-0.5">
              Select your output device for audio playback
            </p>
          </div>
          <select
            value={selectedOutput ?? ''}
            onChange={(e) => handleOutputChange(Number(e.target.value))}
            className="
              w-64 bg-discord-bg-tertiary border border-discord-bg-modifier-active
              rounded-md px-3 py-2 text-discord-text-primary
              focus:ring-2 focus:ring-accent-red focus:border-transparent
              focus:outline-none
            "
          >
            {outputDevices.length === 0 ? (
              <option value="">No speakers found</option>
            ) : (
              outputDevices.map((device) => (
                <option key={device.id} value={device.id}>
                  {device.name}
                </option>
              ))
            )}
          </select>
        </div>

        {/* Test microphone */}
        <div className="flex items-start justify-between gap-4 pt-2">
          <div className="flex-1">
            <label className="text-sm font-medium text-discord-text-primary">
              Microphone Test
            </label>
            <p className="text-sm text-discord-text-muted mt-0.5">
              Records for 2 seconds and plays back so you can hear yourself
            </p>
            {testStatus && (
              <p className="text-sm text-accent-red-text mt-2 animate-pulse">
                {testStatus}
              </p>
            )}
          </div>
          <Button
            onClick={testMicrophone}
            disabled={testing || selectedInput === null || inputDevices.length === 0}
            variant="secondary"
          >
            {testing ? (
              <>
                <RefreshCw size={14} className="animate-spin" />
                <span className="ml-1">Testing...</span>
              </>
            ) : (
              'Test Microphone'
            )}
          </Button>
        </div>
      </div>
    </section>
  );
}
