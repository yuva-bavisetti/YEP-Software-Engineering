import { finishProgress } from "./houseAnimation";
import { useEffect, useRef } from "react";
import * as THREE from "three";
export default function House() {
  const mount = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = mount.current;
    if (!el) return;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    } catch {
      return;
    }
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
    camera.position.set(9, 7, 11);
    camera.lookAt(0, 1, 0);
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.setClearColor(0x000000, 0);
    el.appendChild(renderer.domElement);
    const group = new THREE.Group();
    scene.add(group);
    scene.add(new THREE.AmbientLight(0xffffff, 2));
    const sun = new THREE.DirectionalLight(0xfff3d9, 4);
    sun.position.set(6, 10, 6);
    sun.castShadow = true;
    scene.add(sun);
    const walls: THREE.MeshStandardMaterial[] = [];
    const finishes: {
      material: THREE.MeshStandardMaterial;
      target: THREE.Color;
    }[] = [];
    const landscaping: THREE.Object3D[] = [];
    const box = (
      x: number,
      y: number,
      z: number,
      w: number,
      h: number,
      d: number,
      color: number,
      animated = false,
    ) => {
      const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.75 });
      if (animated) walls.push(mat);
      else finishes.push({ material: mat, target: new THREE.Color(color) });
      const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
      mesh.position.set(x, y, z);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      group.add(mesh);
      return mesh;
    };
    box(0, -0.25, 0, 7, 0.25, 6, 0xdad6c9);
    box(0, -0.05, 0, 6.6, 0.2, 5.6, 0x8d9f73);
    box(0, 1.2, 0, 4.4, 2.5, 3.4, 0xf3eee1, true);
    box(-0.5, 3.2, -0.25, 3.4, 1.6, 2.9, 0xf3eee1, true);
    box(-0.5, 4.05, -0.25, 3.8, 0.18, 3.3, 0x334f45);
    box(0, 2.51, 0, 4.7, 0.16, 3.7, 0xb4a18b);
    box(2, 1.2, 1.78, 0.3, 2.5, 0.18, 0x967356);
    box(-1.4, 1.25, 1.74, 1.1, 1.5, 0.08, 0x426b70);
    box(0.05, 1.25, 1.74, 1.1, 1.5, 0.08, 0x426b70);
    box(1.45, 0.95, 1.76, 0.75, 1.9, 0.09, 0x966c4a);
    box(-0.5, 3.2, 1.22, 2.5, 0.95, 0.06, 0x426b70);
    box(-2.24, 1.25, 0, 0.05, 1.5, 1.9, 0x426b70);
    box(0, 0.08, 2.4, 2.8, 0.12, 1.25, 0xf0e9da);
    box(1.4, 0.02, 2.9, 1.2, 0.08, 0.6, 0xdacdb9);
    for (let i = 0; i < 7; i++)
      box(-1.75 + i * 0.35, 3.2, 1.28, 0.035, 1, 0.03, 0xd6c7ab);
    for (const x of [-2.65, 2.65]) {
      box(x, 0.35, -1.6, 0.14, 0.8, 0.14, 0x86694d);
      const tree = new THREE.Mesh(
        new THREE.SphereGeometry(0.6, 12, 12),
        new THREE.MeshStandardMaterial({ color: 0x526d42 }),
      );
      tree.position.set(x, 1.2, -1.6);
      group.add(tree);
      landscaping.push(tree);
    }
    for (let i = 0; i < 6; i++) {
      const shrub = new THREE.Mesh(
        new THREE.SphereGeometry(0.24, 8, 8),
        new THREE.MeshStandardMaterial({ color: 0x627e4f }),
      );
      shrub.position.set(-2.6 + i * 0.4, 0.25, 2.15);
      group.add(shrub);
      landscaping.push(shrub);
    }
    const resize = () => {
      camera.aspect = el.clientWidth / el.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(el.clientWidth, el.clientHeight);
      renderer.render(scene, camera);
    };
    resize();
    const obs = new ResizeObserver(resize);
    obs.observe(el);
    let frame = 0;
    const start = performance.now();
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const animate = () => {
      const t = (performance.now() - start) / 1000;
      const v = finishProgress(t, reduced);
      walls.forEach((m, index) =>
        m.color
          .copy(new THREE.Color(0xe5e2da))
          .lerp(new THREE.Color(index ? 0x7b9f80 : 0xe3b37b), v),
      );
      finishes.forEach(({ material, target }) =>
        material.color.copy(new THREE.Color(0xd7d4cb)).lerp(target, v),
      );
      landscaping.forEach((o) => o.scale.setScalar(Math.max(0.02, v)));
      group.rotation.y = reduced ? -0.2 : Math.sin(t * 0.17) * 0.13 - 0.2;
      renderer.render(scene, camera);
      if (!reduced) frame = requestAnimationFrame(animate);
    };
    animate();
    return () => {
      cancelAnimationFrame(frame);
      obs.disconnect();
      scene.traverse((o) => {
        if (o instanceof THREE.Mesh) {
          o.geometry.dispose();
          (o.material as THREE.Material).dispose();
        }
      });
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);
  return (
    <div
      ref={mount}
      className="house"
      aria-label="Animated architectural house transforming from neutral to warm finishes"
    >
      <div className="house-fallback">⌂</div>
    </div>
  );
}
