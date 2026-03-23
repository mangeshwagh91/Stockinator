import React, { useEffect, useState, useRef } from 'react';
import Globe from 'react-globe.gl';
import type { GlobeMethods } from 'react-globe.gl';
import * as THREE from 'three';

type GlobeFeature = {
  properties: {
    ISO_A2: string;
    NAME: string;
  };
};

type GlobeFeatureCollection = {
  features: GlobeFeature[];
};

const GlobeScene = () => {
  const globeRef = useRef<GlobeMethods | undefined>(undefined);
  const [countries, setCountries] = useState<GlobeFeatureCollection>({ features: [] });
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);

  useEffect(() => {
    fetch('https://raw.githubusercontent.com/vasturiano/react-globe.gl/master/example/datasets/ne_110m_admin_0_countries.geojson')
      .then(res => res.json())
      .then(setCountries);
  }, []);

  useEffect(() => {
    if (globeRef.current) {
      const controls = globeRef.current.controls();
      if (controls) {
        controls.autoRotate = true;
        controls.autoRotateSpeed = 0.7;
        controls.enablePan = false;
        controls.enableZoom = true;
        controls.minDistance = 200;
        controls.maxDistance = 450;
      }
      
      const scene = globeRef.current.scene();
      scene.children = scene.children.filter((child) => !(child as THREE.Light).isLight);

      // 2. Lighting Adjustments
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.35); // Corrected to 0.35
      scene.add(ambientLight);
      
      const mainLight = new THREE.DirectionalLight(0xffffff, 3.8); // Corrected to 3.8
      mainLight.position.set(150, 100, 100);
      scene.add(mainLight);

      const glowLight = new THREE.PointLight(0x3B82F6, 4.2, 300); // Corrected to 4.2 and #3B82F6
      glowLight.position.set(-150, -50, -50);
      scene.add(glowLight);
    }
  }, []);

  const getPolygonColor = (d: GlobeFeature) => {
    const iso = d.properties.ISO_A2;
    if (['RU', 'CN', 'IR', 'BY', 'KP', 'IL', 'UA'].includes(iso)) return '#995B29'; // Orange/Yellow Countries
    if (['SA', 'PL', 'ID', 'EG', 'DZ', 'PK', 'TR', 'IQ'].includes(iso)) return '#104A35'; // Dark Green Countries
    if (['KZ', 'UZ', 'MM', 'SD', 'LY', 'VN', 'PH', 'BR', 'MX', 'IN'].includes(iso)) return '#0E6889'; // Blue Countries
    return '#14624F'; // Main Green Countries
  };

  return (
    <div className="w-full h-full absolute inset-0 bg-transparent pointer-events-none">
      <div className="pointer-events-auto w-full h-full">
        <Globe
          ref={globeRef}
          backgroundColor="rgba(0,0,0,0)"
          showAtmosphere={true}
          atmosphereColor="#3B82F6"
          atmosphereAltitude={0.32}

          showGlobe={true}
          polygonsData={countries.features}
          polygonCapColor={getPolygonColor}
          polygonSideColor={() => 'rgba(255, 255, 255, 0.1)'}
          polygonStrokeColor={(d: GlobeFeature) => d.properties.ISO_A2 === hoveredCountry ? '#ffffff' : 'rgba(255,255,255,0.3)'}
          polygonAltitude={(d: GlobeFeature) => d.properties.ISO_A2 === hoveredCountry ? 0.08 : 0.01} // Corrected base to 0.01 and hover to 0.08
          polygonsTransitionDuration={300}

          onPolygonHover={(polygon: GlobeFeature | null) => {
            if (polygon) {
              setHoveredCountry(polygon.properties.ISO_A2);
            } else {
              setHoveredCountry(null);
            }
          }}

          
          // Using higher quality earth night textures for the "mottled" look in the image
          globeImageUrl="//unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
          bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
          
          polygonLabel={({ properties: d }: GlobeFeature) => `
            <div style="
              background: rgba(7, 9, 26, 0.95);
              border: 1px solid rgba(255, 255, 255, 0.15);
              padding: 10px 14px;
              border-radius: 12px;
              font-family: 'Inter', sans-serif;
              box-shadow: 0 10px 25px rgba(0,0,0,0.5);
              backdrop-filter: blur(8px);
            ">
              <div style="color: #64748b; font-size: 8px; text-transform: uppercase; letter-spacing: 0.3em; font-weight: 500; margin-bottom: 4px;">Market Region</div>
              <div style="color: #fff; font-size: 13px; font-weight: 700; tracking: tight;">${d.NAME}</div>
              <div style="margin-top: 8px; font-size: 10px; color: ${['RU','CN','IR'].includes(d.ISO_A2) ? '#ef4444' : '#10b981'}; font-weight: 700;">
                  ${['RU','CN','IR'].includes(d.ISO_A2) ? 'CRITICAL RISK' : 'STABLE ASSET'}
              </div>
            </div>
          `}
        />
      </div>

      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_transparent_0%,_rgba(3,7,15,0.4)_50%,_rgba(3,7,15,1)_95%)] pointer-events-none z-10" />
    </div>
  );
};

export default GlobeScene;