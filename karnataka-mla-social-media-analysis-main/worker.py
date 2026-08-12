from apscheduler.schedulers.blocking import BlockingScheduler
from backend.config import settings
from collectors.x_collector import collect as collect_x
from collectors.youtube_collector import collect as collect_youtube


def run_pipeline():
    print("Starting collection cycle...")
    if settings.x_bearer_token:
        collect_x()
    else:
        print("X collector skipped: no X_BEARER_TOKEN.")

    if settings.youtube_api_key:
        collect_youtube()
    else:
        print("YouTube collector skipped: no YOUTUBE_API_KEY.")

    print("Collection cycle complete.")


if __name__ == "__main__":
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_pipeline,
        "interval",
        seconds=settings.poll_interval_seconds,
        next_run_time=None,
        max_instances=1,
    )
    print(f"Worker started. Poll interval: {settings.poll_interval_seconds} seconds.")
    run_pipeline()
    scheduler.start()
