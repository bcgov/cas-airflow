#!/bin/bash
set -e

wal-g backup-push $1
wal-g wal-push $1
