import React from "react";

const PATHS: Record<string, string> = {
  shield: '<path d="M12 2 4 6v6c0 5 3.4 8.5 8 10 4.6-1.5 8-5 8-10V6l-8-4Z"/><path d="m9 12 2 2 4-4"/>',
  alert:
    '<path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/>',
  check: '<circle cx="12" cy="12" r="9"/><path d="m8 12 2.5 2.5L16 9"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  chart: '<path d="M4 20V6M4 20h16"/><path d="M8 20v-6M12 20v-9M16 20v-4M20 20v-11"/>',
  gauge: '<path d="M12 14 8.5 9"/><circle cx="12" cy="14" r="1.5"/><path d="M4 18a9 9 0 1 1 16 0"/>',
  gauge2:
    '<path d="M12 13.5 15.5 9"/><circle cx="12" cy="13.5" r="1.2"/><path d="M4.5 18.5a8 8 0 1 1 15 0"/>',
  play: '<circle cx="12" cy="12" r="9"/><path d="m10 8 6 4-6 4V8Z"/>',
  layers: '<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 13 9 5 9-5"/>',
  brain:
    '<path d="M9 3a3 3 0 0 0-3 3 3 3 0 0 0-2 5 3 3 0 0 0 1 5 3 3 0 0 0 4 3V5a2 2 0 0 0 0-2Z"/><path d="M15 3a3 3 0 0 1 3 3 3 3 0 0 1 2 5 3 3 0 0 1-1 5 3 3 0 0 1-4 3"/>',
  lock: '<rect x="4" y="10" width="16" height="10" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
  server:
    '<rect x="3" y="4" width="18" height="7" rx="2"/><rect x="3" y="13" width="18" height="7" rx="2"/><path d="M7 8h.01M7 17h.01"/>',
  refresh: '<path d="M21 12a9 9 0 1 1-3-6.7"/><path d="M21 3v6h-6"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  filter: '<path d="M3 5h18M6 12h12M10 19h4"/>',
  sort: '<path d="M7 4v16M7 20l-3-3M17 20V4M17 4l3 3"/>',
  chevron: '<path d="m6 9 6 6 6-6"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>',
  spark: '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
  route:
    '<circle cx="6" cy="19" r="2.5"/><circle cx="18" cy="5" r="2.5"/><path d="M8 17.5h6a3 3 0 0 0 0-6H9a3 3 0 0 1 0-6h7"/>',
  shieldAlert:
    '<path d="M12 2 4 6v6c0 5 3.4 8.5 8 10 4.6-1.5 8-5 8-10V6l-8-4Z"/><path d="M12 8v4M12 15h.01"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  list: '<path d="M8 6h13M8 12h13M8 18h13"/><path d="M3 6h.01M3 12h.01M3 18h.01"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  external:
    '<path d="M14 4h6v6"/><path d="M20 4 10 14"/><path d="M19 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h6"/>',
  chevronRight: '<path d="m9 6 6 6-6 6"/>',
  arrowLeft: '<path d="M19 12H5M12 19l-7-7 7-7"/>',
  arrowUpRight: '<path d="M7 17 17 7M8 7h9v9"/>',
  download:
    '<path d="M12 3v12M7 10l5 5 5-5"/><path d="M5 21h14"/>',
  calendar:
    '<rect x="3" y="4.5" width="18" height="16" rx="2"/><path d="M3 9h18M8 2.5v4M16 2.5v4"/>',
  users:
    '<circle cx="9" cy="8" r="3.2"/><path d="M3 20a6 6 0 0 1 12 0"/><path d="M16 6.5a3 3 0 0 1 0 5.6M21 20a5.5 5.5 0 0 0-4-5.3"/>',
  sliders:
    '<path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h9M17 18h3"/><circle cx="15" cy="6" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="15" cy="18" r="2"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
  dot: '<circle cx="12" cy="12" r="3.5"/>',
  bell:
    '<path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 6H4s2-1 2-6"/><path d="M10 19a2 2 0 0 0 4 0"/>',
  inbox:
    '<path d="M3 12h4l2 3h6l2-3h4"/><path d="M5 5h14l2 7v6a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1v-6l2-7Z"/>',
  pencil: '<path d="M12 20h9"/><path d="M16.5 3.5 20 7l-11 11H5v-4l11.5-11.5Z"/>',
  thumbUp:
    '<path d="M7 10v10H4a1 1 0 0 1-1-1v-8a1 1 0 0 1 1-1h3Zm0 0 4-7a2 2 0 0 1 3.6 1.3L14 10h4.5a2 2 0 0 1 2 2.4l-1.2 6A2 2 0 0 1 17.3 20H7"/>',
  thumbDown:
    '<path d="M17 14V4h3a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1h-3Zm0 0-4 7a2 2 0 0 1-3.6-1.3L10 14H5.5a2 2 0 0 1-2-2.4l1.2-6A2 2 0 0 1 6.7 4H17"/>',
};

interface Props {
  name: string;
  className?: string;
  strokeWidth?: number;
}

export default function Icon({ name, className, strokeWidth = 1.8 }: Props) {
  const inner = PATHS[name] ?? PATHS.shield;
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      dangerouslySetInnerHTML={{ __html: inner }}
    />
  );
}
