import { cn } from "@/lib/utils";

export function Badge({
  className,
  variant = "default",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & {
  variant?: "default" | "success" | "warning" | "destructive" | "outline";
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
        variant === "default" && "bg-primary/20 text-primary",
        variant === "success" && "bg-success/20 text-success",
        variant === "warning" && "bg-warning/20 text-warning",
        variant === "destructive" && "bg-destructive/20 text-destructive",
        variant === "outline" && "border border-border text-muted-foreground",
        className
      )}
      {...props}
    />
  );
}
