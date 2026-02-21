/**
 * North Indian style Vedic birth chart visualization
 * Diamond-shaped chart where Ascendant is always at top
 */

import React from 'react';
import { motion } from 'framer-motion';
import type { PlanetPosition } from '../../types/astrology';
import { RASHIS, PLANET_SYMBOLS } from '../../types/astrology';

interface Props {
  planets: PlanetPosition[];
  ascendantRashi: number;
}

// North Indian chart house positions (relative to ascendant)
// House 1 is always at top center

// Positions for planet text in each house
const HOUSE_TEXT_POSITIONS: Record<number, [number, number]> = {
  1: [75, 35],
  2: [85, 25],
  3: [115, 35],
  4: [115, 65],
  5: [125, 100],
  6: [115, 125],
  7: [75, 125],
  8: [35, 125],
  9: [25, 100],
  10: [35, 65],
  11: [25, 35],
  12: [35, 25],
};

export const NorthIndianChart: React.FC<Props> = ({ planets, ascendantRashi }) => {
  // Group planets by house (house = rashi - ascendant + 1)
  const planetsByHouse: Record<number, PlanetPosition[]> = {};
  for (let i = 1; i <= 12; i++) {
    planetsByHouse[i] = [];
  }

  planets.forEach(p => {
    // Calculate house number (1-12)
    let house = ((p.rashiIndex - ascendantRashi + 12) % 12) + 1;
    planetsByHouse[house].push(p);
  });

  // Get rashi for a house
  const getRashiForHouse = (house: number): number => {
    return (ascendantRashi + house - 1) % 12;
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <svg
        viewBox="0 0 150 150"
        className="w-full h-auto"
        style={{ filter: 'drop-shadow(0 4px 20px rgba(59, 130, 246, 0.2))' }}
      >
        {/* Background */}
        <rect x="0" y="0" width="150" height="150" fill="#0d1424" rx="8" />

        {/* Outer border with glow effect */}
        <rect
          x="0" y="0" width="150" height="150"
          fill="none" stroke="#3380ff" strokeWidth="1.5" rx="8"
          style={{ filter: 'drop-shadow(0 0 8px rgba(51, 128, 255, 0.5))' }}
        />

        {/* Center diamond */}
        <polygon
          points="50,50 100,50 100,100 50,100"
          fill="#1a2234"
          stroke="#3380ff"
          strokeWidth="0.5"
          strokeOpacity="0.5"
        />

        {/* Diagonal lines for houses */}
        <line x1="0" y1="0" x2="50" y2="50" stroke="#3380ff" strokeWidth="0.5" strokeOpacity="0.5" />
        <line x1="150" y1="0" x2="100" y2="50" stroke="#3380ff" strokeWidth="0.5" strokeOpacity="0.5" />
        <line x1="0" y1="150" x2="50" y2="100" stroke="#3380ff" strokeWidth="0.5" strokeOpacity="0.5" />
        <line x1="150" y1="150" x2="100" y2="100" stroke="#3380ff" strokeWidth="0.5" strokeOpacity="0.5" />

        {/* Vertical and horizontal lines */}
        <line x1="50" y1="0" x2="50" y2="50" stroke="#3380ff" strokeWidth="0.5" strokeOpacity="0.5" />
        <line x1="100" y1="0" x2="100" y2="50" stroke="#3380ff" strokeWidth="0.5" strokeOpacity="0.5" />
        <line x1="50" y1="100" x2="50" y2="150" stroke="#3380ff" strokeWidth="0.5" strokeOpacity="0.5" />
        <line x1="100" y1="100" x2="100" y2="150" stroke="#3380ff" strokeWidth="0.5" strokeOpacity="0.5" />
        <line x1="0" y1="50" x2="50" y2="50" stroke="#3380ff" strokeWidth="0.5" strokeOpacity="0.5" />
        <line x1="100" y1="50" x2="150" y2="50" stroke="#3380ff" strokeWidth="0.5" strokeOpacity="0.5" />
        <line x1="0" y1="100" x2="50" y2="100" stroke="#3380ff" strokeWidth="0.5" strokeOpacity="0.5" />
        <line x1="100" y1="100" x2="150" y2="100" stroke="#3380ff" strokeWidth="0.5" strokeOpacity="0.5" />

        {/* House numbers and planets */}
        {Object.entries(HOUSE_TEXT_POSITIONS).map(([houseStr, [x, y]]) => {
          const house = parseInt(houseStr);
          const rashi = getRashiForHouse(house);
          const planetsInHouse = planetsByHouse[house];

          return (
            <g key={house}>
              {/* Rashi number */}
              <text
                x={x}
                y={y - 8}
                textAnchor="middle"
                className="text-[8px]"
                fill="#64748b"
                fontFamily="monospace"
              >
                {rashi + 1}
              </text>

              {/* Planets */}
              {planetsInHouse.map((planet, idx) => (
                <motion.text
                  key={planet.planet}
                  x={x}
                  y={y + idx * 10}
                  textAnchor="middle"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.5 + idx * 0.1 }}
                  className="text-[10px] font-bold"
                  fill={planet.isRetrograde ? '#f472b6' : '#8ec7ff'}
                >
                  {PLANET_SYMBOLS[planet.planet] || planet.planet.slice(0, 2)}
                  {planet.isRetrograde && 'ᴿ'}
                </motion.text>
              ))}
            </g>
          );
        })}

        {/* Ascendant label in center */}
        <text x="75" y="72" textAnchor="middle" className="text-[10px]" fill="#3380ff" fontFamily="monospace">
          LAGNA
        </text>
        <text x="75" y="84" textAnchor="middle" className="text-[11px] font-bold" fill="#ffffff">
          {RASHIS[ascendantRashi]}
        </text>
      </svg>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap justify-center gap-3 text-xs text-slate-500">
        {Object.entries(PLANET_SYMBOLS).map(([planet, symbol]) => (
          <div key={planet} className="flex items-center gap-1">
            <span className="font-bold text-cyber-400">{symbol}</span>
            <span>{planet}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
