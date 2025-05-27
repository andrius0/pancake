#!/bin/bash
# Sync root shared/ to each service's shared/ folder
set -e

ROOT_SHARED="pancake-order-system/shared"
SERVICES=(
  "order_service"
  "workflow_worker"
  "activity_workers/analyze_order"
  "activity_workers/inventory"
  "activity_workers/kitchen"
  "activity_workers/notify"
)

for service in "${SERVICES[@]}"; do
  TARGET="pancake-order-system/$service/shared"
  echo "Syncing $ROOT_SHARED -> $TARGET"
  rm -rf "$TARGET"
  mkdir -p "$TARGET"
  cp -r "$ROOT_SHARED/"* "$TARGET/"
done

echo "Shared code sync complete." 