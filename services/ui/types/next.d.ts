/**
 * Type declarations for Next.js modules
 * Resolves errors like: Cannot find module 'next/router' or its corresponding type declarations
 */

declare module 'next/head' {
    import { ReactElement } from 'react';
    export default function Head(props: { children: ReactElement | ReactElement[] }): ReactElement;
}

declare module 'next/router' {
    import { NextRouter } from 'next/dist/client/router';

    export { NextRouter } from 'next/dist/client/router';
    export function useRouter(): NextRouter;
    export function withRouter<T>(component: T): T;
}

declare module 'next/image' {
    import { DetailedHTMLProps, ImgHTMLAttributes } from 'react';

    type ImageProps = DetailedHTMLProps<ImgHTMLAttributes<HTMLImageElement>, HTMLImageElement> & {
        src: string;
        alt: string;
        width?: number;
        height?: number;
        layout?: 'fixed' | 'intrinsic' | 'responsive' | 'fill';
        priority?: boolean;
        placeholder?: 'blur' | 'empty';
        blurDataURL?: string;
    };

    export default function Image(props: ImageProps): JSX.Element;
}
