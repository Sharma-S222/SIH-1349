import argparse
import subprocess
import sys
import time

def main():
    parser = argparse.ArgumentParser(description="Run Multi-Camera Demo")
    parser.add_argument("--camera1", required=True, help="Path to video for CAM_PLATFORM_01")
    parser.add_argument("--camera2", required=True, help="Path to video for CAM_PLATFORM_02")
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000", help="Backend URL")
    parser.add_argument("--loop", action="store_true", help="Loop the videos")
    args = parser.parse_args()

    commands = [
        [
            sys.executable, "scripts/run_live_camera.py",
            "--video-file", args.camera1,
            "--camera-id", "CAM_PLATFORM_01",
            "--backend-url", args.backend_url,
        ] + (["--loop"] if args.loop else []),
        [
            sys.executable, "scripts/run_live_camera.py",
            "--video-file", args.camera2,
            "--camera-id", "CAM_PLATFORM_02",
            "--backend-url", args.backend_url,
        ] + (["--loop"] if args.loop else [])
    ]

    processes = []
    try:
        for cmd in commands:
            print(f"Starting: {' '.join(cmd)}")
            p = subprocess.Popen(cmd)
            processes.append(p)

        while True:
            time.sleep(1)
            for i, p in enumerate(processes):
                if p.poll() is not None:
                    print(f"Process {i} exited with code {p.returncode}")
                    return

    except KeyboardInterrupt:
        print("Interrupt received, stopping cameras...")
    finally:
        for p in processes:
            p.terminate()
        for p in processes:
            p.wait()

if __name__ == "__main__":
    main()
