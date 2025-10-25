"""AddLocksTable Migration."""

from masoniteorm.migrations import Migration


class AddLocksTable(Migration):
    def up(self):
        with self.schema.create('locks') as table:
            # `key` is a reserved word in some SQL dialects (MySQL). Use `lock_key` instead.
            table.string('lock_key').unique()
            table.string('owner')
            table.timestamp('expires_at').nullable()
            table.timestamps()

    def down(self):
        self.schema.drop('locks')
