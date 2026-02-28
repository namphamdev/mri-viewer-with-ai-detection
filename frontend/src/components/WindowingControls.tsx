import { useState } from 'react';
import type { WindowLevel } from '@/types/dicom';
import { WINDOW_PRESETS } from '@/types/dicom';

interface WindowingControlsProps {
  windowLevel: WindowLevel;
  onChange: (wl: WindowLevel) => void;
}

export default function WindowingControls({
  windowLevel,
  onChange,
}: WindowingControlsProps) {
  const [activePreset, setActivePreset] = useState<string>('Brain');

  const handlePresetClick = (preset: (typeof WINDOW_PRESETS)[number]) => {
    setActivePreset(preset.name);
    onChange({
      windowWidth: preset.windowWidth,
      windowCenter: preset.windowCenter,
    });
  };

  const handleManualChange = (field: 'windowWidth' | 'windowCenter', value: string) => {
    const num = parseInt(value, 10);
    if (isNaN(num)) return;
    setActivePreset('');
    onChange({ ...windowLevel, [field]: num });
  };

  return (
    <div className="space-y-3">
      {/* Preset buttons */}
      <div className="grid grid-cols-2 gap-1.5">
        {WINDOW_PRESETS.map((preset) => (
          <button
            key={preset.name}
            onClick={() => handlePresetClick(preset)}
            className={`px-2 py-1.5 rounded text-xs font-medium transition-colors ${
              activePreset === preset.name
                ? 'bg-medical-accent text-white'
                : 'bg-medical-panel border border-medical-border text-medical-text-muted hover:bg-medical-accent/20 hover:text-medical-text'
            }`}
          >
            {preset.name}
          </button>
        ))}
      </div>

      {/* Manual inputs */}
      <div className="space-y-2 pt-2">
        <div className="flex items-center gap-2">
          <label className="text-xs text-medical-text-muted w-14 shrink-0">
            Width
          </label>
          <input
            type="number"
            value={windowLevel.windowWidth}
            onChange={(e) => handleManualChange('windowWidth', e.target.value)}
            className="w-full bg-medical-panel border border-medical-border rounded px-2 py-1 text-sm text-medical-text focus:outline-none focus:border-medical-accent"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-medical-text-muted w-14 shrink-0">
            Center
          </label>
          <input
            type="number"
            value={windowLevel.windowCenter}
            onChange={(e) => handleManualChange('windowCenter', e.target.value)}
            className="w-full bg-medical-panel border border-medical-border rounded px-2 py-1 text-sm text-medical-text focus:outline-none focus:border-medical-accent"
          />
        </div>
      </div>
    </div>
  );
}
