# goal
實作一個script, 當我執行時，可以把本機mac上的 AppleBooks 中的書中的highligh，同步到我的localhost logseq 當中

## spec

### 決定哪些書中的highlight 或筆記要進行同步
1. sync程式會從 target_books.json 中讀取有哪些書需要進行sync， bookItem.sync = true 時，則要進行sync
2. 當執行 script 的時候缺乏 target_books.json 則需要先使用 listbooks 來產生 target_books.json (aka target.json)

### target_books.json
1. Apple Books 裡面所有的書都會存在於此, 使用array, 每個element則為一個 bookItem
2. 新增一本書時, default 不進行同步
3. 每一個bookItem, 可以設定 alias, 用於 logseq page name
4. 執行sync 時，亦會從 Apple Books 裡同步最新的書本資料但會保留故有存在 bookItem 的 sync, alias 狀態

### sync to logseq
1. 每一個bookItem 會對應 logseq 中一個page
2. 該書中的 highlight 和 note (後統一稱 notes) 皆被一起同步到 logseq該書所屬的 page 中
3. 按照 templates 的樣式，使用 logseq format syntax 把內容透過 logseq api 送出至 logseq
4. 若該 bookItem 已經存在 logseq 中，則更新該 page 的內容
5. 當呼叫 logseq api 失敗時，提示錯誤

### template
1. 初版 template 請參考 @template.png
2. 設計一個 template 語法以對應 logseq format. 你需要先survey logseq的語法使用
3. 產生一個獨立的 template file 讓user後續方便修改，測試哪種內容樣式符合user 所需

## plan

### script workflow
1. 檢查 target_books.json 是否存在，若不存在則使用 listbooks 來產生
2. 檢查 logseq api 是否可以連接，若不能則提示錯誤
3. 撈取 AppleBooks 中的 notes, 依照需要sync 的bookItem，透過 template 組出要送出的page內容 
4. 呼叫 logseq api 送出page內容, 若失敗則提示錯誤
