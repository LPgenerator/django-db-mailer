from grappelli.dashboard import modules, Dashboard


class DBMailerDashboard(Dashboard):
    def init_with_context(self, context):
        self.children.append(modules.ModelList(
            title='DBMailer',
            column=1,
            collapsible=True,
            models=(
                'dbmail.models.*',
            ),
        ))
