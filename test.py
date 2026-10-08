    def create_dict(self, res: list[tuple]):
        # thumbs_dict = defaultdict(list[DbImagesItem])
        thumbs = []

        for rel_img_path, rel_thumb_path, mod, fav in res:
            abs_thumb_path_ = Utils.get_abs_thumb_path(rel_thumb_path)

            if not os.path.exists(abs_thumb_path_):
                continue

            qimages = []
            img_bgr = cv2.imread(abs_thumb_path_)
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            for i in Static.THUMB_WID_PIXMAP_SIZE:
                resized = ImgUtils.fit_to_thumb(img_rgb, i * 2)
                qimage = Utils.pyqt_qimage_from_array(resized)
                qimage_scaled = Utils.qimage_scaled_high_dpi(qimage, i)
                qimages.append(qimage_scaled)

            src_qimage = Utils.pyqt_qimage_from_array(img_rgb)
            qimages.append(src_qimage)

            date_ = datetime.fromtimestamp(mod).date()
            month_ = Lng.months[JsonData.lng_index][str(date_.month)]
            month_gen_ = Lng.months_gen[JsonData.lng_index][str(date_.month)]
            day_month_year = f"{date_.day} {month_gen_} {date_.year}"
            month_year = f"{month_} {date_.year}"

            item = DbImagesLoaderItem(
                rel_img_path=rel_img_path,
                rel_thumb_path=rel_thumb_path,
                fav=fav,
                qimages=qimages,
                day_month_year=day_month_year,
                month_year=month_year
            )
            thumbs.append(item)