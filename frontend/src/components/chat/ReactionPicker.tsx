/**
 * Quick emoji picker for message reactions.
 *
 * Shows a row of common emoji for quick reaction selection.
 */

interface ReactionPickerProps {
  onSelect: (emoji: string) => void;
  onClose?: () => void;
}

const QUICK_REACTIONS = [
  { emoji: '\u{1F44D}', label: 'thumbs up' },     //
  { emoji: '\u{2764}\u{FE0F}', label: 'heart' },  //
  { emoji: '\u{1F602}', label: 'laugh' },         //
  { emoji: '\u{1F62E}', label: 'wow' },           //
  { emoji: '\u{1F622}', label: 'sad' },           //
  { emoji: '\u{1F525}', label: 'fire' },          //
  { emoji: '\u{1F44F}', label: 'clap' },          //
  { emoji: '\u{1F389}', label: 'party' },         //
];

export function ReactionPicker({ onSelect, onClose }: ReactionPickerProps) {
  const handleSelect = (emoji: string) => {
    onSelect(emoji);
    onClose?.();
  };

  return (
    <div
      className="flex items-center gap-1 p-2 bg-discord-bg-secondary rounded-lg shadow-lg border border-discord-bg-tertiary"
      onClick={(e) => e.stopPropagation()}
    >
      {QUICK_REACTIONS.map(({ emoji, label }) => (
        <button
          key={label}
          type="button"
          onClick={() => handleSelect(emoji)}
          className="w-8 h-8 flex items-center justify-center rounded hover:bg-discord-bg-modifier-hover transition-colors text-lg"
          title={label}
        >
          {emoji}
        </button>
      ))}
    </div>
  );
}
