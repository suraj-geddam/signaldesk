import { Component, type ErrorInfo, type ReactNode } from "react";

type ErrorBoundaryProps = {
  children: ReactNode;
};

type ErrorBoundaryState = {
  hasError: boolean;
};

export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  public constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  public static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error("signaldesk_frontend_error", { error, errorInfo });
  }

  public render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-stone-50 text-stone-900 flex items-center justify-center px-6">
          <div className="max-w-md rounded-2xl border border-stone-200 bg-white p-8 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-rose-600">
              Unexpected error
            </p>
            <h1 className="mt-3 text-2xl font-semibold">Something went wrong.</h1>
            <p className="mt-3 text-sm leading-6 text-stone-600">
              Refresh the page and try again. If the problem continues, check the browser
              console and backend logs for the correlated request details.
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
