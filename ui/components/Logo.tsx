/**
 * Logo component that displays the SubNetx brand logo with icon
 * Can be reused across the application with customizable size
 */
import { CSSProperties } from 'react';

interface LogoProps {
  theme: {
    primary: string;
  };
  // Size options: 'small' (24px), 'medium' (38px), 'large' (48px)
  size?: 'small' | 'medium' | 'large';
  // Optional className for additional styling
  className?: string;
}

export default function Logo({ theme, size = 'medium', className = '' }: LogoProps) {
  // Define icon sizes based on the size prop
  const iconSizes = {
    small: '24px',
    medium: '38px',
    large: '48px'
  };

  // Define text sizes based on the size prop
  const textSizes = {
    small: '1.2rem',
    medium: '2rem',
    large: '2.5rem'
  };

  const containerStyle: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.75rem'
  };

  return (
    <div style={containerStyle} className={className}>
      <span
        className="material-icons"
        style={{
          color: theme.primary,
          fontSize: iconSizes[size]
        }}
      >
        wifi_tethering
      </span>
      <h1 style={{
        margin: 0,
        color: theme.primary,
        fontSize: textSizes[size],
        fontWeight: 600,
        lineHeight: 1
      }}>
        SubNetx
      </h1>
    </div>
  );
}
