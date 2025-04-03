/**
 * Type declarations for React
 * Resolves the error: Cannot find module 'react' or its corresponding type declarations
 */

declare module 'react' {
    // Basic types
    export type ReactNode = React.ReactElement | string | number | boolean | null | undefined | React.ReactNodeArray;
    export type ReactElement<P = any, T extends string | React.JSXElementConstructor<any> = string | React.JSXElementConstructor<any>> = {
        type: T;
        props: P;
        key: React.Key | null;
    };
    export type JSXElementConstructor<P> = ((props: P) => ReactElement<any, any> | null) | (new (props: P) => React.Component<any, any>);
    export type ReactNodeArray = Array<ReactNode>;
    export type Key = string | number;

    // Hooks
    export function useState<S>(initialState: S | (() => S)): [S, React.Dispatch<React.SetStateAction<S>>];
    export function useEffect(effect: React.EffectCallback, deps?: React.DependencyList): void;
    export function useContext<T>(context: React.Context<T>): T;
    export function useReducer<R extends React.Reducer<any, any>, I>(
        reducer: R,
        initializerArg: I,
        initializer: (arg: I) => React.ReducerState<R>
    ): [React.ReducerState<R>, React.Dispatch<React.ReducerAction<R>>];
    export function useCallback<T extends (...args: any[]) => any>(callback: T, deps: React.DependencyList): T;
    export function useMemo<T>(factory: () => T, deps: React.DependencyList | undefined): T;
    export function useRef<T>(initialValue: T): React.MutableRefObject<T>;

    // Types for hooks
    export type Dispatch<A> = (value: A) => void;
    export type SetStateAction<S> = S | ((prevState: S) => S);
    export type EffectCallback = () => void | (() => void);
    export type DependencyList = ReadonlyArray<any>;
    export type Reducer<S, A> = (prevState: S, action: A) => S;
    export type ReducerState<R extends Reducer<any, any>> = R extends Reducer<infer S, any> ? S : never;
    export type ReducerAction<R extends Reducer<any, any>> = R extends Reducer<any, infer A> ? A : never;
    export interface MutableRefObject<T> {
        current: T;
    }

    // Component classes
    export class Component<P = {}, S = {}> {
        constructor(props: P);
        props: Readonly<P>;
        state: Readonly<S>;
        setState<K extends keyof S>(
            state: ((prevState: Readonly<S>, props: Readonly<P>) => (Pick<S, K> | S | null)) | (Pick<S, K> | S | null),
            callback?: () => void
        ): void;
        forceUpdate(callback?: () => void): void;
        render(): ReactNode;
    }

    // Context
    export interface Context<T> {
        Provider: Provider<T>;
        Consumer: Consumer<T>;
        displayName?: string;
    }
    export interface Provider<T> {
        (props: { value: T; children?: ReactNode }): ReactElement | null;
    }
    export interface Consumer<T> {
        (props: { children: (value: T) => ReactNode }): ReactElement | null;
    }
    export function createContext<T>(defaultValue: T): Context<T>;

    // Other useful exports
    export type CSSProperties = any;
    export function createElement(
        type: string | React.JSXElementConstructor<any>,
        props?: any,
        ...children: React.ReactNode[]
    ): React.ReactElement;
    export function cloneElement<P>(
        element: React.ReactElement<P>,
        props?: Partial<P> & React.Attributes,
        ...children: React.ReactNode[]
    ): React.ReactElement<P>;
}
