"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export function DialogDemo() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">Open Dialog</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Sample consent dialog</DialogTitle>
          <DialogDescription>
            Placeholder for the ConsentDialog component shipped in Story 1.14. The shadcn primitive
            here is already wired to the tokens — focus ring, surfaces, typography all flow from the
            R1 Vermillon palette.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="ghost">Refuse</Button>
          <Button>Accept</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
