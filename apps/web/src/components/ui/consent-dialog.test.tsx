import { describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";

import { ConsentDialog, type ConsentDialogProps, type ConsentMeta } from "./consent-dialog";

const baseProps: Omit<ConsentDialogProps, "onOpenChange" | "onAccept"> = {
  open: true,
  title: "Donner accès à votre conseillère d'orientation",
  description: "Votre conseillère pourra consulter les éléments listés ci-dessous.",
  dataMentioned: ["Métiers recommandés", "Parcours sauvegardés"],
  duration: "12 mois ; révocable à tout moment",
  beneficiary: "Mme Dupont, Lycée Henri-IV",
};

function renderDialog(overrides: Partial<ConsentDialogProps> = {}) {
  const onAccept = vi.fn<(meta: ConsentMeta) => void>();
  const onRefuse = vi.fn();
  const onOpenChange = vi.fn();
  const utils = render(
    <ConsentDialog
      {...baseProps}
      onAccept={onAccept}
      onRefuse={onRefuse}
      onOpenChange={onOpenChange}
      {...overrides}
    />,
  );
  return { onAccept, onRefuse, onOpenChange, ...utils };
}

async function clickAcceptAndGetMeta(
  onAccept: ReturnType<typeof vi.fn<(meta: ConsentMeta) => void>>,
  buttonName: RegExp | string = /Accepter/,
) {
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: buttonName }));
  });
  await waitFor(() => expect(onAccept).toHaveBeenCalled());
  return onAccept.mock.calls.at(-1)![0]!;
}

describe("ConsentDialog", () => {
  it("renders title, description, data mentioned list, duration, and beneficiary verbatim", () => {
    renderDialog();
    expect(screen.getByRole("heading", { name: baseProps.title })).toBeInTheDocument();
    expect(screen.getByText(baseProps.description)).toBeInTheDocument();
    for (const item of baseProps.dataMentioned) {
      expect(screen.getByText(item)).toBeInTheDocument();
    }
    expect(screen.getByText(baseProps.duration)).toBeInTheDocument();
    expect(screen.getByText(baseProps.beneficiary)).toBeInTheDocument();
  });

  it("defaults to 'Accepter' / 'Refuser' labels when acceptLabel / refuseLabel are not provided", () => {
    renderDialog();
    expect(screen.getByRole("button", { name: "Accepter" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Refuser" })).toBeInTheDocument();
  });

  it("empty-string labels fall back to defaults (default-parameter only fires on undefined)", () => {
    renderDialog({ acceptLabel: "", refuseLabel: "" });
    expect(screen.getByRole("button", { name: "Accepter" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Refuser" })).toBeInTheDocument();
  });

  it("clicking accept calls onAccept with ConsentMeta containing a valid ISO 8601 UTC timestamp and a 64-char lowercase hex hash", async () => {
    const { onAccept } = renderDialog();
    const meta = await clickAcceptAndGetMeta(onAccept);
    expect(meta.acceptedAt).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
    expect(meta.contentHash).toMatch(/^[0-9a-f]{64}$/);
  });

  it("clicking refuse calls onRefuse exactly once and triggers onOpenChange(false)", () => {
    const { onRefuse, onOpenChange } = renderDialog();
    fireEvent.click(screen.getByRole("button", { name: "Refuser" }));
    expect(onRefuse).toHaveBeenCalledTimes(1);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("ESC key triggers onRefuse and onOpenChange(false) when not submitting", () => {
    const { onRefuse, onOpenChange } = renderDialog();
    fireEvent.keyDown(document.body, { key: "Escape" });
    expect(onRefuse).toHaveBeenCalledTimes(1);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("ESC key is ignored while isSubmitting=true (consumer cannot lose its in-flight state)", () => {
    const { onRefuse, onOpenChange } = renderDialog({ isSubmitting: true });
    fireEvent.keyDown(document.body, { key: "Escape" });
    expect(onRefuse).not.toHaveBeenCalled();
    expect(onOpenChange).not.toHaveBeenCalled();
  });

  it("both accept and refuse buttons carry the same shadcn size class (h-10 px-4 py-2)", () => {
    renderDialog();
    const accept = screen.getByRole("button", { name: "Accepter" });
    const refuse = screen.getByRole("button", { name: "Refuser" });
    for (const button of [accept, refuse]) {
      expect(button.className).toMatch(/\bh-10\b/);
      expect(button.className).toMatch(/\bpx-4\b/);
      expect(button.className).toMatch(/\bpy-2\b/);
    }
  });

  it("isAcceptDestructive=true renders the accept button with bg-destructive class", () => {
    renderDialog({ isAcceptDestructive: true });
    const accept = screen.getByRole("button", { name: "Accepter" });
    expect(accept.className).toMatch(/\bbg-destructive\b/);
  });

  it("isSubmitting=true disables both buttons, renders an inline spinner, and announces 'Envoi en cours…' to screen readers", () => {
    renderDialog({ isSubmitting: true });
    const accept = screen.getByRole("button", { name: /Accepter/ });
    const refuse = screen.getByRole("button", { name: "Refuser" });
    expect(accept).toBeDisabled();
    expect(refuse).toBeDisabled();
    expect(accept.querySelector("svg.animate-spin")).not.toBeNull();
    expect(screen.getByRole("status").textContent).toBe("Envoi en cours…");
  });

  it("dialog exposes aria-busy reflecting isSubmitting", () => {
    const { rerender } = renderDialog({ isSubmitting: false });
    expect(screen.getByRole("dialog").getAttribute("aria-busy")).toBe("false");
    rerender(
      <ConsentDialog {...baseProps} isSubmitting onAccept={vi.fn()} onOpenChange={vi.fn()} />,
    );
    expect(screen.getByRole("dialog").getAttribute("aria-busy")).toBe("true");
  });

  it("contentHash is deterministic — same props produce identical hashes over 10 invocations", async () => {
    const hashes = new Set<string>();
    for (let i = 0; i < 10; i += 1) {
      const onAccept = vi.fn<(meta: ConsentMeta) => void>();
      const { unmount } = render(
        <ConsentDialog {...baseProps} open onOpenChange={vi.fn()} onAccept={onAccept} />,
      );
      const meta = await clickAcceptAndGetMeta(onAccept);
      hashes.add(meta.contentHash);
      unmount();
    }
    expect(hashes.size).toBe(1);
  });

  it("contentHash is sensitive to title — changing it yields a different hash", async () => {
    const onAcceptA = vi.fn<(meta: ConsentMeta) => void>();
    const onAcceptB = vi.fn<(meta: ConsentMeta) => void>();

    const { unmount } = render(
      <ConsentDialog {...baseProps} open onOpenChange={vi.fn()} onAccept={onAcceptA} />,
    );
    const metaA = await clickAcceptAndGetMeta(onAcceptA);
    unmount();

    render(
      <ConsentDialog
        {...baseProps}
        title="Un titre complètement différent"
        open
        onOpenChange={vi.fn()}
        onAccept={onAcceptB}
      />,
    );
    const metaB = await clickAcceptAndGetMeta(onAcceptB);

    expect(metaA.contentHash).not.toBe(metaB.contentHash);
  });

  it("contentHash is sensitive to isAcceptDestructive — true vs false yield different hashes", async () => {
    const onAcceptA = vi.fn<(meta: ConsentMeta) => void>();
    const onAcceptB = vi.fn<(meta: ConsentMeta) => void>();

    const { unmount } = render(
      <ConsentDialog
        {...baseProps}
        isAcceptDestructive={false}
        open
        onOpenChange={vi.fn()}
        onAccept={onAcceptA}
      />,
    );
    const metaA = await clickAcceptAndGetMeta(onAcceptA);
    unmount();

    render(
      <ConsentDialog
        {...baseProps}
        isAcceptDestructive={true}
        open
        onOpenChange={vi.fn()}
        onAccept={onAcceptB}
      />,
    );
    const metaB = await clickAcceptAndGetMeta(onAcceptB);

    expect(metaA.contentHash).not.toBe(metaB.contentHash);
  });

  it("contentHash is sensitive to acceptLabel — different label yields different hash", async () => {
    const onAcceptA = vi.fn<(meta: ConsentMeta) => void>();
    const onAcceptB = vi.fn<(meta: ConsentMeta) => void>();

    const { unmount } = render(
      <ConsentDialog
        {...baseProps}
        acceptLabel="Accepter"
        open
        onOpenChange={vi.fn()}
        onAccept={onAcceptA}
      />,
    );
    const metaA = await clickAcceptAndGetMeta(onAcceptA);
    unmount();

    render(
      <ConsentDialog
        {...baseProps}
        acceptLabel="Envoyer mon profil"
        open
        onOpenChange={vi.fn()}
        onAccept={onAcceptB}
      />,
    );
    const metaB = await clickAcceptAndGetMeta(onAcceptB, "Envoyer mon profil");

    expect(metaA.contentHash).not.toBe(metaB.contentHash);
  });

  it("re-entry guard: rapid double-click on Accept fires onAccept only once", async () => {
    const onAccept = vi.fn<(meta: ConsentMeta) => void>();
    render(<ConsentDialog {...baseProps} open onOpenChange={vi.fn()} onAccept={onAccept} />);
    const accept = screen.getByRole("button", { name: "Accepter" });
    await act(async () => {
      fireEvent.click(accept);
      fireEvent.click(accept);
      fireEvent.click(accept);
    });
    await waitFor(() => expect(onAccept).toHaveBeenCalled());
    expect(onAccept).toHaveBeenCalledTimes(1);
  });

  it("onAccept rejection is logged via console.error and the guard is freed so the user can retry", async () => {
    const rejecting = vi
      .fn<(meta: ConsentMeta) => Promise<void>>()
      .mockRejectedValueOnce(new Error("audit endpoint 500"))
      .mockResolvedValueOnce(undefined);

    const errorSpy = vi.spyOn(console, "error").mockImplementation(() => {});

    render(<ConsentDialog {...baseProps} open onOpenChange={vi.fn()} onAccept={rejecting} />);
    const accept = screen.getByRole("button", { name: "Accepter" });

    await act(async () => {
      fireEvent.click(accept);
    });
    await waitFor(() => expect(rejecting).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(errorSpy).toHaveBeenCalled());

    // Guard must be released — second click reaches onAccept again.
    await act(async () => {
      fireEvent.click(accept);
    });
    await waitFor(() => expect(rejecting).toHaveBeenCalledTimes(2));

    errorSpy.mockRestore();
  });

  it("the dialog has aria-labelledby pointing to the title element and aria-describedby pointing to the description element", () => {
    renderDialog();
    const dialog = screen.getByRole("dialog");
    const titleId = dialog.getAttribute("aria-labelledby");
    const descriptionId = dialog.getAttribute("aria-describedby");
    expect(titleId).toBeTruthy();
    expect(descriptionId).toBeTruthy();
    expect(document.getElementById(titleId!)?.textContent).toBe(baseProps.title);
    expect(document.getElementById(descriptionId!)?.textContent).toBe(baseProps.description);
  });
});
