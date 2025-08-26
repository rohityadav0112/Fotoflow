from django.apps import AppConfig
import threading
class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        from accounts.background_tasks.notification import messages
        from accounts.background_tasks.worker import worker_fu
        import threading

        # Start 5 daemon threads for handling post background tasks
        for _ in range(5):
            t = threading.Thread(target=worker_fu, daemon=True)
            t.start()

        # Wrapper function to start your scheduler
        def start_scheduler():
            messages.start_scheduler()  # Your scheduler function in messages.py

        # Start scheduler in a daemon thread (runs once)
        threading.Thread(target=start_scheduler, daemon=True).start()


# class AccountsConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'accounts'
    
#     def ready(self):
#         # from .post_tasks import worker
#         from accounts.background_tasks.worker import worker_fu


#         # Start 5 daemon threads for post request processing
#         for _ in range(5):
#             t = threading.Thread(target=worker_fu, daemon=True)
#             t.start()
# ---------------------------------------------------------------------------------------------------------
# from django.apps import AppConfig
# import threading

# class AccountsConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'accounts'

#     def ready(self):
#         from accounts.background_tasks.notification import messages
#         from accounts.background_tasks.worker import worker_fu
#         for _ in range(5):
#             t = threading.Thread(target=worker_fu, daemon=True)
#             t.start()

#         def start_scheduler():
#             messages.start_scheduler()  # <--- You'll define this in your messages.py

#         # Only start once to avoid multiple schedulers in dev
#         threading.Thread(target=start_scheduler, daemon=True).start()
