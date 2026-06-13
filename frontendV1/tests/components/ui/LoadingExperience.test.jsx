import { act, fireEvent, render, screen } from "@testing-library/react";

import LoadingExperience from "../../../src/components/ui/LoadingExperience.jsx";

describe("LoadingExperience", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.clearAllTimers();
    jest.useRealTimers();
  });

  test("does not flash for work that finishes before the visibility delay", () => {
    const { unmount } = render(<LoadingExperience label="Loading cart" delayMs={200} />);

    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    unmount();

    act(() => {
      jest.advanceTimersByTime(250);
    });

    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  test("shows contextual messages and advances only while still mounted", () => {
    render(
      <LoadingExperience
        label="Loading cart"
        delayMs={0}
        messageIntervalMs={1000}
      />
    );

    expect(screen.getByText("Opening your cart")).toBeInTheDocument();

    act(() => {
      jest.advanceTimersByTime(1000);
    });

    expect(screen.getByText("Checking stock and current prices")).toBeInTheDocument();
  });

  test("offers retry after a request takes too long", () => {
    const onRetry = jest.fn();
    render(
      <LoadingExperience
        label="Loading payment"
        delayMs={0}
        timeoutMs={2000}
        onRetry={onRetry}
      />
    );

    act(() => {
      jest.advanceTimersByTime(2000);
    });

    expect(screen.getByText("This is taking longer than expected")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /try again/i }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
