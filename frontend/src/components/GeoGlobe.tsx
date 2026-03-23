import { useEffect, useRef } from "react";
import * as THREE from "three";

type Region = {
  points: Array<[number, number]>;
  fill: string;
};

const REGIONS: Region[] = [
  { fill: "#2ea56f", points: [[-168, 10], [-150, 8], [-138, 26], [-124, 31], [-108, 49], [-95, 54], [-88, 44], [-102, 24], [-116, 14], [-142, 4], [-160, 6]] },
  { fill: "#1e8f63", points: [[-83, 12], [-70, 8], [-58, -2], [-52, -18], [-56, -32], [-66, -52], [-76, -40], [-80, -18], [-82, 2]] },
  { fill: "#278f73", points: [[-11, 37], [2, 45], [18, 55], [34, 56], [42, 47], [30, 39], [22, 33], [8, 36], [-2, 35]] },
  { fill: "#cc433f", points: [[36, 42], [50, 52], [70, 62], [98, 71], [130, 70], [156, 59], [168, 48], [162, 36], [138, 24], [114, 30], [86, 36], [64, 30], [46, 33]] },
  { fill: "#3194ce", points: [[64, 35], [86, 31], [106, 27], [126, 24], [122, 14], [104, 9], [84, 5], [70, 11], [60, 20]] },
  { fill: "#d58f2f", points: [[-18, 30], [2, 34], [18, 26], [34, 18], [36, 2], [28, -12], [16, -26], [2, -31], [-10, -20], [-16, -2]] },
  { fill: "#2c9fa1", points: [[40, 20], [54, 27], [70, 30], [80, 25], [90, 18], [90, 7], [74, 0], [60, 4], [48, 10], [40, 16]] },
  { fill: "#cc433f", points: [[40, 31], [55, 35], [74, 37], [78, 28], [66, 21], [50, 21], [40, 25]] },
  { fill: "#cb7847", points: [[30, 36], [40, 45], [55, 44], [62, 36], [52, 31], [38, 30]] },
  { fill: "#2f9f64", points: [[108, -10], [118, -14], [130, -20], [146, -28], [154, -40], [143, -45], [124, -38], [112, -26], [108, -17]] },
  { fill: "#2a8f83", points: [[46, -13], [52, -20], [50, -26], [44, -23], [42, -17]] },
];

const latLonToUv = (lon: number, lat: number, width: number, height: number) => {
  const x = ((lon + 180) / 360) * width;
  const y = ((90 - lat) / 180) * height;
  return { x, y };
};

const buildPoliticalTexture = () => {
  const width = 2048;
  const height = 1024;
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d");

  if (!ctx) return null;

  const gradient = ctx.createLinearGradient(0, 0, 0, height);
  gradient.addColorStop(0, "#042458");
  gradient.addColorStop(0.45, "#0b3b74");
  gradient.addColorStop(1, "#03204a");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, width, height);

  ctx.globalAlpha = 0.25;
  for (let i = 0; i < 320; i += 1) {
    const gx = Math.random() * width;
    const gy = Math.random() * height;
    const r = 8 + Math.random() * 24;
    const g = ctx.createRadialGradient(gx, gy, 0, gx, gy, r);
    g.addColorStop(0, "rgba(86,180,255,0.35)");
    g.addColorStop(1, "rgba(86,180,255,0)");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(gx, gy, r, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.globalAlpha = 0.92;
  ctx.lineWidth = 2;
  ctx.strokeStyle = "rgba(33, 191, 255, 0.34)";

  for (const region of REGIONS) {
    ctx.beginPath();
    region.points.forEach(([lon, lat], index) => {
      const { x, y } = latLonToUv(lon, lat, width, height);
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.closePath();
    ctx.fillStyle = region.fill;
    ctx.fill();
    ctx.stroke();
  }

  ctx.globalAlpha = 0.26;
  ctx.strokeStyle = "#77b4f2";
  ctx.lineWidth = 1;
  for (let lon = -180; lon <= 180; lon += 15) {
    ctx.beginPath();
    for (let lat = -90; lat <= 90; lat += 5) {
      const { x, y } = latLonToUv(lon, lat, width, height);
      if (lat === -90) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.stroke();
  }
  for (let lat = -75; lat <= 75; lat += 15) {
    ctx.beginPath();
    for (let lon = -180; lon <= 180; lon += 5) {
      const { x, y } = latLonToUv(lon, lat, width, height);
      if (lon === -180) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.stroke();
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 8;
  texture.needsUpdate = true;
  return texture;
};

const GeoGlobe = () => {
  const mountRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const scene = new THREE.Scene();
    scene.background = null;

    const camera = new THREE.PerspectiveCamera(45, mount.clientWidth / mount.clientHeight, 0.1, 1000);
    camera.position.z = 4.2;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    mount.appendChild(renderer.domElement);

    const globeGeometry = new THREE.SphereGeometry(1.25, 112, 112);
    const politicalTexture = buildPoliticalTexture();
    const globeMaterial = new THREE.MeshStandardMaterial({
      map: politicalTexture ?? undefined,
      color: new THREE.Color("#6fc6ff"),
      emissive: new THREE.Color("#0f2b5a"),
      emissiveIntensity: 0.38,
      metalness: 0.24,
      roughness: 0.78,
    });

    const globe = new THREE.Mesh(globeGeometry, globeMaterial);
    scene.add(globe);

    // A subtle wireframe shell gives the geopolitical map vibe from the reference.
    const shell = new THREE.Mesh(
      new THREE.SphereGeometry(1.275, 64, 64),
      new THREE.MeshBasicMaterial({
        color: new THREE.Color("#13d9ff"),
        wireframe: true,
        transparent: true,
        opacity: 0.12,
      }),
    );
    scene.add(shell);

    const atmosphere = new THREE.Mesh(
      new THREE.SphereGeometry(1.36, 64, 64),
      new THREE.MeshBasicMaterial({
        color: new THREE.Color("#39d7ff"),
        transparent: true,
        opacity: 0.13,
        blending: THREE.AdditiveBlending,
        side: THREE.BackSide,
      }),
    );
    scene.add(atmosphere);

    const orbitGroup = new THREE.Group();
    const orbitMaterial = new THREE.LineBasicMaterial({ color: "#f3b848", transparent: true, opacity: 0.75 });
    const arc1 = new THREE.EllipseCurve(0, 0, 2.12, 1.18, 0, Math.PI * 2);
    const arc2 = new THREE.EllipseCurve(0, 0, 2.16, 1.42, 0, Math.PI * 2);
    const line1 = new THREE.Line(new THREE.BufferGeometry().setFromPoints(arc1.getPoints(170).map((p) => new THREE.Vector3(p.x, p.y, 0))), orbitMaterial);
    const line2 = new THREE.Line(new THREE.BufferGeometry().setFromPoints(arc2.getPoints(170).map((p) => new THREE.Vector3(p.x, p.y, 0))), orbitMaterial);
    line1.rotation.set(1.05, 0.34, 0.35);
    line2.rotation.set(0.75, -0.72, -0.18);
    orbitGroup.add(line1, line2);
    scene.add(orbitGroup);

    const markerGeom = new THREE.SphereGeometry(0.03, 16, 16);
    const markerMaterial = new THREE.MeshBasicMaterial({ color: "#34ffb5" });
    const marker = new THREE.Mesh(markerGeom, markerMaterial);
    marker.position.set(0.4, 0.95, 0.7);
    scene.add(marker);

    const ambient = new THREE.AmbientLight("#a4d6ff", 0.95);
    const keyLight = new THREE.DirectionalLight("#51e6ff", 1.4);
    keyLight.position.set(4, 2, 4);
    const backLight = new THREE.DirectionalLight("#2f59d9", 0.92);
    backLight.position.set(-5, -2, -4);

    scene.add(ambient, keyLight, backLight);

    const starsGeometry = new THREE.BufferGeometry();
    const starCount = 900;
    const positions = new Float32Array(starCount * 3);

    for (let i = 0; i < starCount * 3; i += 3) {
      positions[i] = (Math.random() - 0.5) * 30;
      positions[i + 1] = (Math.random() - 0.5) * 30;
      positions[i + 2] = (Math.random() - 0.5) * 30;
    }

    starsGeometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    const stars = new THREE.Points(
      starsGeometry,
      new THREE.PointsMaterial({ color: "#b9d3ff", size: 0.018, transparent: true, opacity: 0.8 }),
    );
    scene.add(stars);

    let rafId = 0;
    const animate = () => {
      rafId = requestAnimationFrame(animate);
      globe.rotation.y += 0.0015;
      globe.rotation.x = Math.sin(Date.now() * 0.00027) * 0.09;
      shell.rotation.y += 0.0014;
      shell.rotation.x = globe.rotation.x;
      atmosphere.rotation.y += 0.0012;
      orbitGroup.rotation.y -= 0.0017;
      marker.scale.setScalar(1 + Math.sin(Date.now() * 0.006) * 0.24);
      stars.rotation.y += 0.00015;
      renderer.render(scene, camera);
    };

    animate();

    const onResize = () => {
      if (!mount) return;
      camera.aspect = mount.clientWidth / mount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth, mount.clientHeight);
    };

    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener("resize", onResize);
      mount.removeChild(renderer.domElement);

      globeGeometry.dispose();
      markerGeom.dispose();
      globeMaterial.dispose();
      markerMaterial.dispose();
      (line1.material as THREE.Material).dispose();
      (line2.material as THREE.Material).dispose();
      line1.geometry.dispose();
      line2.geometry.dispose();
      starsGeometry.dispose();
      (stars.material as THREE.Material).dispose();
      if (politicalTexture) politicalTexture.dispose();
      renderer.dispose();
    };
  }, []);

  return <div ref={mountRef} className="geo-globe-canvas" aria-hidden="true" />;
};

export default GeoGlobe;
