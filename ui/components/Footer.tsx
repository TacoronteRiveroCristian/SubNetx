/**
 * Footer component that displays copyright information and links
 * Used across multiple pages for consistent navigation and branding
 */
import { CSSProperties } from 'react';

interface FooterProps {
  theme: {
    cardBackground: string;
    border: string;
    text: string;
    primary: string;
  };
}

export default function Footer({ theme }: FooterProps) {
  // Estilo del footer para asegurar que aparezca en la parte inferior
  const footerStyle: CSSProperties = {
    backgroundColor: theme.cardBackground,
    padding: '0.8rem',
    borderTop: `1px solid ${theme.border}`,
    width: '100%',
    boxSizing: 'border-box',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '0.5rem',
    flexShrink: 0,
    position: 'relative',
    bottom: 0,
    left: 0,
    zIndex: 10,
    marginTop: 'auto'
  };

  const copyrightStyle: CSSProperties = {
    fontSize: '0.85rem',
    color: theme.text,
    opacity: 0.8
  };

  const linksContainerStyle: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '1.5rem'
  };

  const linkStyle: CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '0.4rem',
    color: theme.text,
    textDecoration: 'none',
    transition: 'color 0.2s',
    fontSize: '0.85rem'
  };

  return (
    <footer style={footerStyle}>
      <div style={copyrightStyle}>
        © {new Date().getFullYear()} SubNetx. Released under the MIT License.
      </div>
      <div style={linksContainerStyle}>
        <a
          href="mailto:tacoronteriverocristian@gmail.com"
          style={linkStyle}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = theme.primary;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = theme.text;
          }}
        >
          <span className="material-icons" style={{ fontSize: '16px' }}>email</span>
          Contact
        </a>
        <a
          href="https://github.com/TacoronteRiveroCristian/SubNetx"
          target="_blank"
          rel="noopener noreferrer"
          style={linkStyle}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = theme.primary;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = theme.text;
          }}
        >
          <span className="material-icons" style={{ fontSize: '16px' }}>code</span>
          GitHub
        </a>
      </div>
    </footer>
  );
}
