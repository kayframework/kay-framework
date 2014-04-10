=============================
デコレーター
=============================

.. module:: kay.utils.decorators

ビューデコレーター
=============================

Kay は appengine 環境での開発に便利なデコレーター関数を
いくつか提供しています。これらのデコレーターは、
viewでよく使われそうな機能を提供します。

.. function:: maintenance_check(endpoint='_internal/maintenance_page')

    ``maintenance_check()`` デコレーターは Appengine データストアが
    メンテナンスモードの状態になっているかを確認し、メンテナンスモード
    の場合、メンテナンス画面にリダイレクトしてくれます。デフォルトは
    '_internal/maintenance_page' という URL ルーティングエンドポイントに
    リダイレクトしますが、 ``endpoint`` という引数で指定することができます。

    ::

        @maintenance_check
        def my_view(request):
            # ...
            return response

.. function:: cron_only()

    ``cron_only()`` デコレーターは Appengine の cron
    サービスからのリクエストかどうかを確認する
    デコレーターです。適切な HTTP ヘッダーを確認し、
    cron リクエストではない場合、403 Forbidden 
    レスポンスを返す。開発の時に便利な設定項目が一つあります。
    :attr:`DEBUG`を`True`に設定すると、
    開発サーバーで動かしている場合は全てのリクエストを通す。

    ::

        @cron_only
        def my_cron_view(request):
            # ...
            return response

ユーティリティデコレーター
=============================

.. function:: retry_on_timeout(retries=3, secs=1)

    ``retry_on_timeout()`` デコレーターを使うと
    データストアにアクセスする処理を
    実行する間にデータストアのAPIタイムアウトが
    起こった場合、retriesで指定された回数リトライを行う。
    ラップされる関数は、複数回実行される可能性があるので、
    複数回実行しても問題がないように
    `冪等 <http://ja.wikipedia.org/wiki/%E5%86%AA%E7%AD%89>`_
    にしなければなりません。

    ::

        @retry_on_timeout(retries=5)
        def my_writer_func():
            # Some datastore operation
            return

.. function:: auto_adapt_to_methods()

    ``auto_adapt_to_methods()`` デコレーターは、
    他のデコレーターをラップするデコレーターです。
    このデコレーターでラップされたデコレーターは、
    self引数がない関数と同様に、
    self引数が渡されるメソッドも適切に
    ラップすることができるようになります。

    ::

        @auto_adapt_to_methods
        def my_decorator(func):
            def new_func():
                # ...
                return
            return new_func
