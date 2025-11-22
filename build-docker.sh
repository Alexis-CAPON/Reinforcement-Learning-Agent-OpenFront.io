#!/bin/bash
# Build script for OpenFront.io RL Docker image

set -e  # Exit on error

echo "========================================="
echo "OpenFront.io RL Docker Build Script"
echo "========================================="
echo ""

# Default values
PLATFORM="linux/amd64"
TAG="openfrontio-rl:latest"
NO_CACHE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        --no-cache)
            NO_CACHE="--no-cache"
            shift
            ;;
        --arm64)
            PLATFORM="linux/arm64"
            shift
            ;;
        --amd64)
            PLATFORM="linux/amd64"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --platform PLATFORM    Target platform (default: linux/amd64)"
            echo "  --tag TAG             Docker image tag (default: openfrontio-rl:latest)"
            echo "  --no-cache            Build without cache"
            echo "  --arm64               Shortcut for --platform linux/arm64"
            echo "  --amd64               Shortcut for --platform linux/amd64"
            echo "  --help                Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Build for AMD64 (GPU servers)"
            echo "  $0 --arm64            # Build for ARM64 (Mac M1/M2)"
            echo "  $0 --no-cache         # Force rebuild without cache"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "Build configuration:"
echo "  Platform: $PLATFORM"
echo "  Tag: $TAG"
echo "  Cache: $([ -z "$NO_CACHE" ] && echo "enabled" || echo "disabled")"
echo ""

# Check if running on Mac ARM64
if [[ "$OSTYPE" == "darwin"* ]] && [[ "$(uname -m)" == "arm64" ]]; then
    echo "⚠️  Detected Mac ARM64"
    if [[ "$PLATFORM" == "linux/amd64" ]]; then
        echo "⚠️  Building AMD64 image on ARM64 Mac will be slower (emulation)"
        echo "   This is correct for GPU server deployment"
        echo "   Press Ctrl+C to cancel, or wait 5 seconds to continue..."
        sleep 5
    fi
fi

echo ""
echo "Starting Docker build..."
echo "This may take 10-20 minutes for first build"
echo ""

# Build the image
docker build \
    --platform "$PLATFORM" \
    $NO_CACHE \
    -t "$TAG" \
    -f Dockerfile \
    .

BUILD_EXIT=$?

echo ""
if [ $BUILD_EXIT -eq 0 ]; then
    echo "========================================="
    echo "✅ Build successful!"
    echo "========================================="
    echo ""
    echo "Image: $TAG"
    echo "Platform: $PLATFORM"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Test locally:"
    echo "   docker run --rm $TAG python3 -c 'import torch; print(torch.__version__)'"
    echo ""
    echo "2. Save for server transfer:"
    echo "   docker save $TAG | gzip > openfrontio-rl.tar.gz"
    echo ""
    echo "3. Or push to registry:"
    echo "   docker tag $TAG YOUR_REGISTRY/$TAG"
    echo "   docker push YOUR_REGISTRY/$TAG"
    echo ""
else
    echo "========================================="
    echo "❌ Build failed!"
    echo "========================================="
    echo ""
    echo "Common issues:"
    echo "  - Missing system dependencies"
    echo "  - Network issues downloading packages"
    echo "  - Insufficient disk space"
    echo ""
    echo "Try building with --no-cache to force rebuild"
    exit 1
fi
