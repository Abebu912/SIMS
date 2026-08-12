from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'users'

    def ready(self):
        # Monkeypatch django.template.context.Context.__copy__ to be resilient
        # to un-copyable objects (e.g., builtin `super` instances) found in
        # context dicts. This is a fallback to keep admin pages rendering
        # even if some third-party or project code accidentally puts
        # non-dict-like objects into template contexts.
        try:
            from django.template import context as ctxmod
            orig_copy = getattr(ctxmod.Context, '__copy__', None)

            def safe_copy(self):
                try:
                    if orig_copy:
                        return orig_copy(self)
                except Exception:
                    # fall through to a safer copy
                    pass

                # Build a sanitized Context object with only dict-like
                # entries so subsequent template operations don't attempt
                # to set attributes on un-copyable objects.
                try:
                    new_dicts = []
                    for d in getattr(self, 'dicts', []):
                        if isinstance(d, dict):
                            new_dicts.append(d)
                        else:
                            try:
                                new_dicts.append({'__unserializable__': repr(d)})
                            except Exception:
                                new_dicts.append({'__unserializable__': str(type(d))})

                    new_ctx = ctxmod.Context()
                    new_ctx.dicts = new_dicts
                    return new_ctx
                except Exception:
                    # As a last resort, return an empty Context
                    return ctxmod.Context()

            ctxmod.Context.__copy__ = safe_copy
        except Exception as exc:
            # Don't crash startup if monkeypatch fails; log for debugging.
            try:
                print('users.apps.UsersConfig.ready() monkeypatch failed:', exc)
            except Exception:
                pass
