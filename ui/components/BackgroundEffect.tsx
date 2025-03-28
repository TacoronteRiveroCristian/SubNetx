/**
 * Animated background effect component with grid and dots
 * Responds to mouse movement and theme changes
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

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const backgroundStyle: CSSProperties = {
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100vw',
    height: '100vh',
    backgroundColor: theme.background,
    overflow: 'hidden',
    zIndex: 0
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
      radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, ${theme.primary}15 0%, transparent 35%),
      repeating-linear-gradient(rgba(127, 127, 127, 0.03) 0px, rgba(127, 127, 127, 0.03) 1px, transparent 1px, transparent 50px),
      repeating-linear-gradient(90deg, rgba(127, 127, 127, 0.03) 0px, rgba(127, 127, 127, 0.03) 1px, transparent 1px, transparent 50px)
    `,
    maskImage: 'radial-gradient(circle at center, black 30%, transparent 70%)',
    WebkitMaskImage: 'radial-gradient(circle at center, black 30%, transparent 70%)',
    transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
    opacity: 0.8,
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
      radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, ${theme.primary}10 0%, transparent 25%),
      radial-gradient(circle at 50% 50%, rgba(127, 127, 127, 0.08) 2px, transparent 2.5px),
      radial-gradient(circle at 50% 50%, rgba(127, 127, 127, 0.05) 1px, transparent 1px)
    `,
    backgroundSize: '100% 100%, 28px 28px, 24px 24px',
    backgroundPosition: 'center',
    maskImage: 'radial-gradient(circle at center, black 40%, transparent 70%)',
    WebkitMaskImage: 'radial-gradient(circle at center, black 40%, transparent 70%)',
    animation: 'floatDots 120s linear infinite',
    opacity: 0.9,
    willChange: 'transform',
    backfaceVisibility: 'hidden',
    transformStyle: 'preserve-3d'
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
      `}</style>

      <div style={backgroundStyle}>
        <div style={gridStyle}></div>
        <div style={dotsStyle}></div>
      </div>
    </>
  );
}
