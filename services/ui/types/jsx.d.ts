/**
 * Type declarations for JSX elements in React
 * Resolves the error: JSX element implicitly has type 'any' because no interface 'JSX.IntrinsicElements' exists
 */

import 'react';

declare global {
    namespace JSX {
        interface IntrinsicElements {
            [elemName: string]: any;
        }
    }
}
