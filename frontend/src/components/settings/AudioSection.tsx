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
          setSelectedInput(result.inputs[0].id);
        }
        if (result.outputs?.length && selectedOutput === null) {
          setSelectedOutput(result.outputs[0].id);
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
        const fileResult = await api.call((a) => a.get_file(result.id));
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
      <div className="space-y-4 p-4 bg-cosmic-surface/50 rounded-xl border border-cosmic-border">
        <h3 className="text-lg font-semibold text-cosmic-text">Audio</h3>
        <p className="text-cosmic-muted">Loading devices...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4 bg-cosmic-surface/50 rounded-xl border border-cosmic-border">
      <h3 className="text-lg font-semibold text-cosmic-text">Audio</h3>

      {/* Microphone selection */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-cosmic-muted">
          Microphone
        </label>
        <select
          value={selectedInput ?? ''}
          onChange={(e) => handleInputChange(Number(e.target.value))}
          className="w-full bg-cosmic-bg text-cosmic-text rounded-lg px-3 py-2 border border-cosmic-border focus:border-cosmic-accent focus:outline-none"
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
      <div className="space-y-2">
        <label className="block text-sm font-medium text-cosmic-muted">
          Speaker
        </label>
        <select
          value={selectedOutput ?? ''}
          onChange={(e) => handleOutputChange(Number(e.target.value))}
          className="w-full bg-cosmic-bg text-cosmic-text rounded-lg px-3 py-2 border border-cosmic-border focus:border-cosmic-accent focus:outline-none"
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

      {/* Test microphone button */}
      <div className="space-y-2">
        <button
          onClick={testMicrophone}
          disabled={testing || selectedInput === null || inputDevices.length === 0}
          className="px-4 py-2 bg-cosmic-accent hover:bg-cosmic-accent/80 disabled:bg-cosmic-surface disabled:text-cosmic-muted disabled:cursor-not-allowed text-white rounded-lg transition-colors"
        >
          {testing ? 'Testing...' : 'Test Microphone'}
        </button>

        {testStatus && (
          <p className="text-sm text-cosmic-accent animate-pulse">{testStatus}</p>
        )}

        <p className="text-xs text-cosmic-muted">
          Records for 2 seconds and plays back so you can hear yourself.
        </p>
      </div>
    </div>
  );
}
