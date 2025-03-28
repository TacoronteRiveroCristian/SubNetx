/**
 * Animated background effect component with grid and dots
 * Responds to mouse movement and theme changes
 * Creates an immersive 3D space effect with parallax movement
 */
import { CSSProperties, useEffect, useState } from 'react';

interface BackgroundEffectProps {
  theme: {
    background: string;
    primary: string;
  };
}

export default function BackgroundEffect({ theme }: BackgroundEffectProps) {
  const [mousePosition, setMousePosition] = useState({ x: 50, y: 50 });
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    // Start with a delay to allow the page to load first
    const timer = setTimeout(() => setIsActive(true), 300);

    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      clearTimeout(timer);
    };
  }, []);

  const backgroundStyle: CSSProperties = {
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100vw',
    height: '100vh',
    backgroundColor: theme.background,
    overflow: 'hidden',
    zIndex: 0,
    transition: 'background-color 0.5s ease',
  };

  const gridStyle: CSSProperties = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    width: '200vw',
    height: '200vh',
    transformOrigin: 'center',
    transform: `translate(-50%, -50%)
                perspective(2000px)
                rotateX(${(mousePosition.y - 50) * 0.1}deg)
                rotateY(${(mousePosition.x - 50) * 0.1}deg)`,
    backgroundImage: `
      radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, ${theme.primary}20 0%, transparent 45%),
      repeating-linear-gradient(rgba(127, 127, 127, 0.04) 0px, rgba(127, 127, 127, 0.04) 1px, transparent 1px, transparent 50px),
      repeating-linear-gradient(90deg, rgba(127, 127, 127, 0.04) 0px, rgba(127, 127, 127, 0.04) 1px, transparent 1px, transparent 50px)
    `,
    maskImage: 'radial-gradient(circle at center, black 30%, transparent 70%)',
    WebkitMaskImage: 'radial-gradient(circle at center, black 30%, transparent 70%)',
    transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.8s ease',
    opacity: isActive ? 0.85 : 0,
    willChange: 'transform',
    backfaceVisibility: 'hidden',
    transformStyle: 'preserve-3d'
  };

  const dotsStyle: CSSProperties = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    width: '200vw',
    height: '200vh',
    transform: 'translate(-50%, -50%)',
    backgroundImage: `
      radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, ${theme.primary}15 0%, transparent 35%),
      radial-gradient(circle at 50% 50%, rgba(127, 127, 127, 0.1) 2px, transparent 2.5px),
      radial-gradient(circle at 50% 50%, rgba(127, 127, 127, 0.07) 1px, transparent 1px)
    `,
    backgroundSize: '100% 100%, 28px 28px, 24px 24px',
    backgroundPosition: 'center',
    maskImage: 'radial-gradient(circle at center, black 40%, transparent 70%)',
    WebkitMaskImage: 'radial-gradient(circle at center, black 40%, transparent 70%)',
    animation: 'floatDots 120s linear infinite',
    opacity: isActive ? 0.9 : 0,
    transition: 'opacity 0.8s ease',
    willChange: 'transform',
    backfaceVisibility: 'hidden',
    transformStyle: 'preserve-3d'
  };

  // Add a new starfield effect
  const starsStyle: CSSProperties = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    width: '200vw',
    height: '200vh',
    transform: `translate(-50%, -50%) rotate(${mousePosition.x * 0.02}deg)`,
    backgroundImage: `
      radial-gradient(circle at 25% 25%, ${theme.primary}10 1px, transparent 1px),
      radial-gradient(circle at 75% 75%, ${theme.primary}10 1px, transparent 1px),
      radial-gradient(circle at 25% 75%, ${theme.primary}10 1px, transparent 1px),
      radial-gradient(circle at 75% 25%, ${theme.primary}10 1px, transparent 1px),
      radial-gradient(circle at 34% 86%, ${theme.primary}10 1px, transparent 1px),
      radial-gradient(circle at 45% 61%, ${theme.primary}10 1px, transparent 1px),
      radial-gradient(circle at 82% 37%, ${theme.primary}10 1px, transparent 1px)
    `,
    backgroundSize: '150px 150px, 200px 200px, 130px 130px, 120px 120px, 180px 180px, 110px 110px, 160px 160px',
    opacity: isActive ? 0.8 : 0,
    transition: 'opacity 0.8s ease, transform 0.5s ease',
    animation: 'twinkling 8s infinite alternate'
  };

  return (
    <>
      <style jsx global>{`
        @keyframes floatDots {
          from {
            transform: translate(-50%, -50%) rotate(0deg);
          }
          to {
            transform: translate(-50%, -50%) rotate(360deg);
          }
        }

        @keyframes twinkling {
          0% { opacity: 0.3; }
          50% { opacity: 0.8; }
          100% { opacity: 0.3; }
        }
      `}</style>

      <div style={backgroundStyle}>
        <div style={gridStyle}></div>
        <div style={dotsStyle}></div>
        <div style={starsStyle}></div>
      </div>
    </>
  );
}
