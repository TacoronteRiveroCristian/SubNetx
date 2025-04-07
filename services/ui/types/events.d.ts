/**
 * Type declarations for event handlers in React
 * Resolves the error: Parameter 'e' implicitly has an 'any' type
 */

import React from 'react';

declare global {
    type ReactMouseEvent = React.MouseEvent<HTMLElement>;
    type ReactChangeEvent = React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>;
}
